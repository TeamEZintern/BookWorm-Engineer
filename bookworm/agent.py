import json
import time

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from .commands import VALID_MODES, CommandResult, handle_command
from .config import Config
from .prompts import build_system_prompt
from .tools import ToolRegistry, call_tool

HALLUNCINATION_THRESHOLD = 0.75


class Agent:
    def __init__(
        self,
        config: Config,
        client: ChatOpenRouter,
        tool_registry: ToolRegistry,
        system_prompt: str,
    ) -> None:
        self.config = config
        self.client = client
        self.tool_registry = tool_registry
        self.bound_model = client.bind_tools(
            tools=self.tool_registry.schema,
            tool_choice="auto",
        )
        self._mode = "plan"
        self.messages: list = [
            SystemMessage(content=system_prompt)
        ]
        self.sources_dir = self.config.working_dir / ".bookworm" / "sources"

    def _set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}"
            )
        self._mode = mode
        self.messages[0] = SystemMessage(content=build_system_prompt(self.config, mode))

    def _print_banner(self) -> None:
        print("=========== BookWorm Engineer ==========\n")
        print("Hello I am BookWorm Engineer, your research and coding assistant.")
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

            self.messages.append(HumanMessage(content=user_prompt))
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
            response = self.bound_model.invoke(self.messages)

            if hasattr(response, "content_blocks") and response.content_blocks:
                for block in response.content_blocks:
                    if isinstance(block, dict) and block.get("type") == "reasoning":
                        print("Thinking: ", block.get("reasoning", ""), "\n")

            self.messages.append(response)

            if not response.tool_calls:
                content = response.content
                if isinstance(content, list):
                    return "".join(
                        block["text"] if isinstance(block, dict) and block.get("type") == "text" else str(block)
                        for block in content
                    ) or ""
                return content or ""

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_arguments = json.dumps(tool_call["args"])

                print(f"Calling {tool_name} with arguments {tool_arguments}\n")

                tool_result = call_tool(
                    registry=self.tool_registry,
                    name=tool_name,
                    arguments_json=tool_arguments,
                )

                print(f"Result: {tool_result}\n")

                self.messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                    )
                )

                if response.usage_metadata:
                    context_used = response.usage_metadata["input_tokens"] / self.config.context_window

                    if context_used >= HALLUNCINATION_THRESHOLD:
                        self.messages.append(
                            SystemMessage(
                                content=(
                                    f" WARNING: {context_used: .2%} of context window used."
                                    "Conclude this processing loop as soon as possible"
                                ),
                            )
                        )
