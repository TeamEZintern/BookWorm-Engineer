import time
from typing import Any

from openai import OpenAI

from .agent_events import TurnCancelledError, TurnEventHandler
from .commands import VALID_MODES, CommandResult, handle_command
from .config import Config
from .llm import complete_with_retry
from .prompts import build_system_prompt
from .tools import ToolRegistry, call_tool

HALLUNCINATION_THRESHOLD = 0.75


def _api_tool_call_from_part(part: dict[str, Any]) -> dict[str, Any]:
    """Convert a GUI tool_call content part to OpenAI API tool_calls shape."""
    return {
        "id": part["id"],
        "type": "function",
        "function": {
            "name": part["name"],
            "arguments": part.get("arguments", "{}"),
        },
    }


def _api_messages_from_assistant_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert ordered GUI assistant parts into OpenAI-compatible messages."""
    messages: list[dict[str, Any]] = []
    pending_tool_calls: list[dict[str, Any]] = []

    def flush_tool_calls() -> None:
        nonlocal pending_tool_calls
        if not pending_tool_calls:
            return
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": pending_tool_calls,
            }
        )
        pending_tool_calls = []

    for part in parts:
        part_type = part.get("type")
        if part_type == "reasoning":
            continue
        if part_type == "tool_call":
            pending_tool_calls.append(_api_tool_call_from_part(part))
            continue
        if part_type == "tool_result":
            flush_tool_calls()
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": part["tool_call_id"],
                    "content": part.get("content", ""),
                }
            )
            continue
        if part_type == "final_answer":
            flush_tool_calls()
            messages.append(
                {
                    "role": "assistant",
                    "content": part.get("text", ""),
                }
            )

    flush_tool_calls()
    return messages


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
        self._cancel_requested = False

    def request_cancel(self) -> None:
        """Ask the current turn to stop at the next safe checkpoint."""
        self._cancel_requested = True

    def clear_cancel(self) -> None:
        self._cancel_requested = False

    def _check_cancelled(self) -> None:
        if self._cancel_requested:
            raise TurnCancelledError()

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Valid modes: {', '.join(sorted(VALID_MODES))}"
            )
        self._mode = mode
        self.messages[0] = {
            "role": "system",
            "content": build_system_prompt(self.config, mode),
        }

    def _print_banner(self) -> None:
        print("\nHello I am BookWorm Engineer, your research and coding assistant.")
        print("How may I help you?")
        print("Type '/exit' or '/quit' to stop.\n")

    def _get_source_names(self) -> list[str]:
        if not self.sources_dir.is_dir():
            return []
        try:
            return sorted(
                f.name
                for f in self.sources_dir.iterdir()
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
                set_mode=self.set_mode,
            )
            if result == CommandResult.EXIT:
                return
            if result == CommandResult.HANDLED:
                continue

            checkpoint = len(self.messages)
            self.messages.append({"role": "user", "content": user_prompt})
            start_time = time.time()

            try:
                response_text = self.run_turn()
            except Exception as exc:
                del self.messages[checkpoint:]
                print(f"\n[error] Could not complete that request: {exc}\n")
                continue

            print(f"\n{response_text}\n")
            elapsed = time.time() - start_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Time taken: {int(hours):02}:{int(minutes):02}:{seconds:05.2f}\n")

    def load_conversation(self, chat_messages: list[dict[str, Any]]) -> None:
        """Rebuild agent history from persisted GUI chat messages."""
        self.messages = [
            {"role": "system", "content": build_system_prompt(self.config, self._mode)}
        ]
        for message in chat_messages:
            role = message.get("role")
            if role not in {"user", "assistant"}:
                continue
            content = message.get("content", "")
            if role == "user":
                self.messages.append({"role": "user", "content": content})
                continue
            if isinstance(content, list):
                self.messages.extend(_api_messages_from_assistant_parts(content))

    def run_turn(self, event_handler: TurnEventHandler | None = None) -> str:
        """Run one agent turn, optionally emitting progress events."""
        self.clear_cancel()
        turn_tool_calls: list[dict[str, Any]] = []
        try:
            while True:
                self._check_cancelled()
                if event_handler is None:
                    final_content = self._run_non_streaming_leg(
                        turn_tool_calls,
                        event_handler,
                    )
                else:
                    final_content = self._run_streaming_leg(
                        turn_tool_calls,
                        event_handler,
                    )

                if final_content is not None:
                    if event_handler and event_handler.on_turn_complete:
                        event_handler.on_turn_complete(final_content, turn_tool_calls)
                    return final_content
        except TurnCancelledError:
            raise
        except Exception as exc:
            if event_handler and event_handler.on_error:
                event_handler.on_error(str(exc))
            raise

    def _build_completion_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.config.llm_model,
            "messages": self.messages,
            "tools": self.tool_registry.schema,
            "tool_choice": "auto",
        }
        if "openrouter.ai" in self.config.llm_base_url:
            kwargs["extra_body"] = {
                "reasoning": {
                    "effort": "low",
                }
            }
        return kwargs

    def _request_completion(self, **overrides: Any) -> Any:
        """Call the LLM with retry policy from llm.py."""
        kwargs = self._build_completion_kwargs()
        kwargs.update(overrides)
        return complete_with_retry(client=self.client, **kwargs)

    def _append_context_warning(self, usage: Any) -> None:
        if usage is None:
            return
        context_used = usage.prompt_tokens / self.config.context_window
        if context_used >= HALLUNCINATION_THRESHOLD:
            self.messages.append(
                {
                    "role": "system",
                    "content": (
                        f" WARNING: {context_used: .2%} of context window used."
                        "Conclude this processing loop as soon as possible"
                    ),
                }
            )

    def _run_non_streaming_leg(
        self,
        turn_tool_calls: list[dict[str, Any]],
        event_handler: TurnEventHandler | None,
    ) -> str | None:
        response = self._request_completion()
        reply = response.choices[0].message

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": reply.content or "",
        }

        if reply.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in reply.tool_calls
            ]

        self.messages.append(assistant_message)

        if not reply.tool_calls:
            return reply.content or ""

        for tool_call in reply.tool_calls:
            self._execute_tool_call(
                tool_call.id,
                tool_call.function.name,
                tool_call.function.arguments,
                turn_tool_calls,
                event_handler,
            )
            self._append_context_warning(response.usage)

        return None

    def _run_streaming_leg(
        self,
        turn_tool_calls: list[dict[str, Any]],
        event_handler: TurnEventHandler,
    ) -> str | None:
        stream = self._request_completion(stream=True)

        content_parts: list[str] = []
        tool_calls_acc: dict[int, dict[str, Any]] = {}
        usage = None

        try:
            for chunk in stream:
                self._check_cancelled()
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                reasoning_text = getattr(delta, "reasoning", None) or getattr(
                    delta, "reasoning_content", None
                )
                if reasoning_text and event_handler.on_reasoning_delta:
                    event_handler.on_reasoning_delta(reasoning_text)

                if delta.content:
                    content_parts.append(delta.content)
                    if event_handler.on_text_delta:
                        event_handler.on_text_delta(delta.content)

                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        if index not in tool_calls_acc:
                            tool_calls_acc[index] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        accumulated = tool_calls_acc[index]
                        if tool_call_delta.id:
                            accumulated["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                accumulated["function"]["name"] += tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                accumulated["function"]["arguments"] += (
                                    tool_call_delta.function.arguments
                                )

                if getattr(chunk, "usage", None) is not None:
                    usage = chunk.usage
        except TurnCancelledError:
            self._append_partial_streaming_assistant(content_parts, tool_calls_acc)
            raise

        final_content = "".join(content_parts)
        tool_calls_list = [tool_calls_acc[index] for index in sorted(tool_calls_acc)]

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": final_content,
        }
        if tool_calls_list:
            assistant_message["tool_calls"] = tool_calls_list

        self.messages.append(assistant_message)

        if not tool_calls_list:
            return final_content

        for tool_call in tool_calls_list:
            self._execute_tool_call(
                tool_call["id"],
                tool_call["function"]["name"],
                tool_call["function"]["arguments"],
                turn_tool_calls,
                event_handler,
            )
            self._append_context_warning(usage)

        return None

    def _append_partial_streaming_assistant(
        self,
        content_parts: list[str],
        tool_calls_acc: dict[int, dict[str, Any]],
    ) -> None:
        """Persist streamed assistant text when a turn is stopped mid-stream."""
        final_content = "".join(content_parts)
        if not final_content:
            return
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": final_content,
        }
        self.messages.append(assistant_message)

    def _execute_tool_call(
        self,
        call_id: str,
        tool_name: str,
        tool_arguments: str,
        turn_tool_calls: list[dict[str, Any]],
        event_handler: TurnEventHandler | None,
    ) -> None:
        self._check_cancelled()
        if event_handler and event_handler.on_tool_call_started:
            event_handler.on_tool_call_started(tool_name, tool_arguments, call_id)

        tool_result = call_tool(
            registry=self.tool_registry,
            name=tool_name,
            arguments_json=tool_arguments,
        )

        turn_tool_calls.append(
            {
                "id": call_id,
                "name": tool_name,
                "arguments": tool_arguments,
                "result": tool_result,
            }
        )

        if event_handler and event_handler.on_tool_result:
            event_handler.on_tool_result(call_id, tool_result)

        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": tool_result,
            }
        )