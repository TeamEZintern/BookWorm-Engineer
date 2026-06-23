import json
import time
from typing import Any

from openai import (
    OpenAI,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

from .commands import VALID_MODES, CommandResult, handle_command
from .config import Config
from .prompts import build_system_prompt
from .tools import ToolRegistry, call_tool
from .llm import complete_with_retry

HALLUNCINATION_THRESHOLD = 0.75
MAX_API_RETRIES = 4
RETRY_BASE_DELAY = 2.0


class Agent:
    def __init__(
        self,
        config: Config,
        client: OpenAI,
        tool_registry: ToolRegistry,
        system_prompt: str,
    ) -> None:
        self.config = config
        self.client = client
        self.tool_registry = tool_registry
        self._mode = "plan"
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.sources_dir = self.config.working_dir / ".bookworm" / "sources"

    def _set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}"
            )
        self._mode = mode
        self.messages[0] = {"role": "system", "content": build_system_prompt(self.config, mode)}

    def _print_banner(self) -> None:
        print("\nHello I am BookWorm Engineer, your research and coding assistant.")
        print("How may I help you?")
        print("Type 'exit' or 'quit' to stop.\n")

    def _get_source_names(self) -> list[str]:
        if not self.sources_dir.is_dir():
            return []
        try:
            return sorted(
                f.name for f in self.sources_dir.iterdir()
                if f.is_file() and f.suffix.lower() in {".pdf", ".txt", ".md"}
            )
        except OSError:
            return []

    def _print_status(self) -> None:
        sources = self._get_source_names()
        print(f"Mode: {self._mode.capitalize()}")
        print(f"CWD: {self.config.working_dir}")
        print(f"Sources: {', '.join(sources) if sources else '-none-'}")

    def run(self) -> None:
        self._print_banner()

        while True:
            self._print_status()

            try:
                user_prompt = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting BookWorm Engineer. Goodbye!")
                return

            print()

            if not user_prompt:
                continue

            result = handle_command(
                text=user_prompt,
                working_dir=self.config.working_dir,
                set_mode=self._set_mode
            )
            if result == CommandResult.EXIT:
                return
            if result == CommandResult.HANDLED:
                continue

            checkpoint = len(self.messages)
            self.messages.append({"role":"user", "content": user_prompt})
            start_time = time.time()

            # try: 
            #     response_text = self._run_turn()
            # except Exception as exc: 
            #     raise RuntimeError(f"Failed to generate response: {exc}") from exc
            
            # print(f"\n{response_text}\n")

            try: 
                response_text = self._run_turn()
            except Exception as exc: 
                del self.messages[checkpoint:]
                print(f"\n[error] Could not complete that request: {exc}\n")
                continue

            print(f"\n{response_text}\n")

            elapsed = time.time() - start_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Time taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}\n")

    def _create_completion(self):
        """
        Call the LLM, retrying transient failures with exponential backoff

        On overload a provider/gateway can return a non-JSON body (an exmpty or HTML page, or an SSE stream).
        The SDK then throws json.JSONDecodeError while parsing the reponse - note that's a *raw* json error, not an
        openai error type, so it escapes unless caught explicitly. Treat taht, plus connection/ rate-limit / 5xx errors,
        as retryable. Real 4xx client errors are deliebrately NOT caught - retrying cant fix them, and hiding them would just 
        delay the real diagnosis
        """
        last_exc: Exception | None = None
        for attempt in range(1, MAX_API_RETRIES + 1):
            try: 
                response = self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=self.messages,
                tools=self.tool_registry.schema,
                tool_choice="auto",
                extra_body={
                    "reasoning": {
                        "effort": "low",  # options: "low" | "medium" | "high"
                    }
                },
            )
            except (
                APIConnectionError,
                RateLimitError,
                InternalServerError,
                json.JSONDecodeError,
            ) as exc: 
                last_exc = exc
                if attempt == MAX_API_RETRIES:
                    break
                delay = RETRY_BASE_DELAY * 2 ** (attempt - 1)
                print(
                    f"  ! LLM request failed ({type(exc).__name__}); "
                    f"retrying in {delay:.0f}s "
                    f"(attempt {attempt}/{MAX_API_RETRIES})..."
                )
                time.sleep(delay)

                raise RuntimeError(
                    f"LLM request failed after {MAX_API_RETRIES} attemps: {last_exc}"
                ) from last_exc
            
            return response
            
        

    def _run_turn(self) -> str:
        while True:
            response = complete_with_retry(
                client=self.client,
                model=self.config.llm_model,
                messages=self.messages,
                tools=self.tool_registry.schema,
                tool_choice="auto",
                extra_body={
                    "reasoning": {
                        "effort": "low",  # options: "low" | "medium" | "high"
                    }
                },
            )

            reply = response.choices[0].message

            assistant_message: dict[str,Any] = {
                "role" : "assistant",
                "content" : reply.content or "",
            }

            if reply.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id" : tool_call.id,
                        "type" : tool_call.type,
                        "function" : {
                            "name" : tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in reply.tool_calls
                ]
            
            self.messages.append(assistant_message)

            if not reply.tool_calls:
                return reply.content or ""
            
            for tool_call in reply.tool_calls:
                tool_name = tool_call.function.name
                tool_arguments = tool_call.function.arguments

                tool_result = call_tool(
                    registry=self.tool_registry,
                    name=tool_name,
                    arguments_json=tool_arguments,
                )

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id" : tool_call.id,
                        "content": tool_result,
                    }
                )

                if response.usage is not None: 
                    context_used = response.usage.prompt_tokens / self.config.context_window

                    if context_used >= HALLUNCINATION_THRESHOLD:
                        self.messages.append(
                            {
                                "role" : "system",
                                "content" : (
                                    f" WARNING: {context_used: .2%} of context window used."
                                    "Conclude this processing loop as soon as possible"
                                ),
                            }
                        )
