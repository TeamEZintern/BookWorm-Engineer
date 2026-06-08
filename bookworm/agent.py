import json
import time
from typing import Any

from openai import OpenAI

from .config import Config
from .tools import ToolRegistry, call_tool

HALLUNCINATION_THRESHOLD = 0.75

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
        self.messages: list[dict[str,any]] = [
            {"role": "system", "content": system_prompt}
        ]

    def run(self) -> None: 
        print("BookWorm Engineer is ready.")
        print("Type 'exit' or 'quit' to stop.\n")
        
        while True: 
            user_prompt = input("> ").strip()

            if user_prompt.lower() in {"exit", "quit"}:
                print("Exiting Bookworm Engineer. Goodbye!")
                return 
            
            if not user_prompt:
                continue

            self.message.append({"role":"user", "content": user_prompt})
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

            if getattr(reply, "re0soning", None):
                print("Thinking: ", reply.resoning, "\n")

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
                                "roles" : "system",
                                "content" : (
                                    f" WARNING: {context_used: .2%} of context window used."
                                    "Conflude this processing loop as soon as possible"
                                ),
                            }
                        )
