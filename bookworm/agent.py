import json
import time
from typing import Any

from openai import OpenAI

from .config import Config
from .prompts import build_system_prompt
from .tools import ToolRegistry, call_tool

HALLUNCINATION_THRESHOLD = 0.75
VALID_MODES = {"plan", "build", "research"}


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

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.messages[0] = {"role": "system", "content": build_system_prompt(self.config, mode)}

    def _print_banner(self) -> None:
        print("=========== BookWorm Engineer ==========\n")
        print("Hello I am BookWorm Engineer, your research and coding assistant.")
        print("How may I help you?")
        print("Type 'exit' or 'quit' to stop.\n")

    def _get_source_names(self) -> list[str]:
        sources_dir = self.config.working_dir / ".bookworm" / "sources"
        if not sources_dir.is_dir():
            return []
        try:
            return sorted(
                f.name for f in sources_dir.iterdir()
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

            if user_prompt.lower() in {"exit", "quit"}:
                print("Exiting BookWorm Engineer. Goodbye!")
                return

            if user_prompt.lower().startswith("mode switch "):
                new_mode = user_prompt[12:].strip().lower()
                if new_mode in VALID_MODES:
                    self._set_mode(new_mode)
                    print(f"Switched to {self._mode.capitalize()} mode.\n")
                else:
                    print(f"Unknown mode '{new_mode}'. Available: {', '.join(sorted(VALID_MODES))}\n")
                continue

            if user_prompt.lower() == "help":
                print(
                    "Commands:\n"
                    "  mode switch <plan|build|research>  — change the agent's mode\n"
                    "  exit / quit                         — leave BookWorm Engineer\n"
                    "  help                                — show this message\n"
                )
                continue

            self.messages.append({"role":"user", "content": user_prompt})
            start_time = time.time()

            try: 
                response_text = self._run_turn()
            except Exception as exc: 
                raise RuntimeError(f"Failed to generate response: {exc}") from exc
            
            print(f"\n{response_text}\n")
            elapsed = time.time() - start_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Time taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}\n")

    def _run_turn(self) -> str:
        while True:
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

            reply = response.choices[0].message

            if getattr(reply, "reasoning", None):
                print("Thinking: ", reply.reasoning, "\n")

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

                print(f"Calling {tool_name} with arguments {tool_arguments}\n")

                tool_result = call_tool(
                    registry=self.tool_registry,
                    name=tool_name,
                    arguments_json=tool_arguments,
                )

                print(f"Result: {tool_result}\n")

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
