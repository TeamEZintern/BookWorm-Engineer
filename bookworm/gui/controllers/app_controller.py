"""
App Controller

Top-level controller for the BookWorm GUI. Owns the main window view
(``ui_main_window``), instantiates the side panel and main panel controllers,
injects their widgets into the splitter, and coordinates loading a chat's
conversation into the main panel.
"""

import uuid
from datetime import datetime

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from bookworm.agent import Agent
from bookworm.commands import CommandResult, handle_command
from bookworm.llm import create_client
from bookworm.prompts import build_system_prompt
from bookworm.tools import create_tool_registry

from ..agent_runner import AgentRunner
from ..ask_user_bridge import AskUserBridge
from ..config import GUIConfig
from ..models import Chat, ChatStore, Message, default_chat_name
from ..themes import build_stylesheet
from ..views.window.ui_main_window import Ui_MainWindow
from .main_panel_controller import MainPanelController
from .side_panel_controller import SidePanelController


class AppController(QObject):
    """
    Main controller wiring together the window, side panel, and main panel.

    Exposes ``self.window`` (a ``QMainWindow``) for the CLI to ``show()``.
    """

    def __init__(self, config, gui_config: GUIConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.gui_config = gui_config
        chats_dir = config.working_dir / ".bookworm" / "chats"
        self.store = ChatStore(chats_dir)
        self.current_chat_id = None
        self._loading_conversation = False
        self._turn_chat_id: str | None = None
        self._turn_tool_calls: list = []
        self._turn_reasoning = ""

        self.window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(gui_config.theme))

        self.window.setWindowTitle(gui_config.window_title)
        self.window.setMinimumSize(gui_config.window_width, gui_config.window_height)

        self.splitter = self.window.findChild(QSplitter, "mainSplitter")

        self.side_panel_controller = SidePanelController(gui_config)
        self.main_panel_controller = MainPanelController(gui_config)
        self.side_panel_controller.chat_selected.connect(self.on_chat_selected)
        self.side_panel_controller.chat_created.connect(self.on_chat_created)
        self.side_panel_controller.chat_renamed.connect(self.on_chat_renamed)
        self.side_panel_controller.chat_deleted.connect(self.on_chat_deleted)
        self.side_panel_controller.theme_toggle_requested.connect(self.on_theme_toggle)
        self.main_panel_controller.messages_changed.connect(self._on_messages_changed)
        self.main_panel_controller.draft_changed.connect(self._on_draft_changed)
        self.main_panel_controller.agent_turn_requested.connect(self._on_agent_turn_requested)
        self.main_panel_controller.agent_turn_stop_requested.connect(
            self._on_agent_turn_stop_requested
        )
        self.main_panel_controller.mode_change_requested.connect(
            self._on_mode_change_requested
        )
        self.main_panel_controller.special_command_submitted.connect(
            self._on_special_command_submitted
        )

        self._ask_user_bridge = AskUserBridge(self.window)
        tool_registry = create_tool_registry(
            config,
            ask_user_fn=self._ask_user_bridge.ask,
        )
        self.agent = Agent(
            config=config,
            client=create_client(config),
            tool_registry=tool_registry,
            system_prompt=build_system_prompt(config),
        )
        self.main_panel_controller.update_mode(self.agent.mode)
        self._agent_runner = AgentRunner(self)
        self._agent_runner.text_delta.connect(self._on_agent_text_delta)
        self._agent_runner.tool_call_started.connect(
            self._on_agent_tool_call_started
        )
        self._agent_runner.tool_result.connect(self._on_agent_tool_result)
        self._agent_runner.reasoning_delta.connect(self._on_agent_reasoning_delta)
        self._agent_runner.turn_complete.connect(self._on_agent_turn_complete)
        self._agent_runner.turn_cancelled.connect(self._on_agent_turn_cancelled)
        self._agent_runner.error.connect(self._on_agent_error)

        self.splitter.addWidget(self.side_panel_controller.widget)
        self.splitter.addWidget(self.main_panel_controller.widget)
        self.splitter.setSizes([
            gui_config.side_panel_width,
            self.window.width() - gui_config.side_panel_width,
        ])

        self.window.statusBar().showMessage("Ready")

        self.load_initial_data()
        self._apply_theme_to_controllers()

    def _apply_theme_to_controllers(self):
        self.side_panel_controller.apply_theme(self.gui_config.theme)

    def _default_welcome_message(self) -> dict:
        return {
            "role": "assistant",
            "content": [
                {
                    "type": "final_answer",
                    "text": (
                        "Welcome to Bookworm GUI! This is a graphical interface for the "
                        "Bookworm AI coding assistant. You can create, rename, and delete "
                        "chats, and chat with the agent."
                    ),
                }
            ],
            "timestamp": datetime.now().isoformat(),
        }

    def _create_default_chat(self) -> Chat:
        now = datetime.now()
        chat = Chat(
            chat_id=str(uuid.uuid4()),
            name=default_chat_name(now),
            created_at=now,
            updated_at=now,
            messages=[self._default_welcome_message()],
        )
        self.store.add(chat)
        return chat

    def load_initial_data(self):
        """Load chats from disk and show the first conversation."""
        self.store.load()

        if self.store.is_empty():
            self._create_default_chat()

        self.update_side_panel()
        chats = self.store.all()
        if chats:
            self._select_chat(chats[0])

    def update_side_panel(self):
        """Update the side panel with current chats."""
        self.side_panel_controller.update_chat_list(self.store.all())

    def _save_current_chat(self) -> None:
        """Persist the active chat into the current chat JSON file."""
        if self._loading_conversation or not self.current_chat_id:
            return
        chat = self.store.get(self.current_chat_id)
        if chat is None:
            return
        include_streaming = (
            self._agent_runner.is_running()
            and self._turn_chat_id == self.current_chat_id
        )
        chat.messages = self.main_panel_controller.get_message_dicts(
            include_streaming=include_streaming
        )
        chat.draft = self.main_panel_controller.get_draft()
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _persist_turn_chat(self, chat_id: str) -> None:
        """Save the chat that owns an in-flight turn, including partial assistant text."""
        chat = self.store.get(chat_id)
        if chat is None:
            return
        if chat_id == self.current_chat_id:
            chat.messages = self.main_panel_controller.get_message_dicts(
                include_streaming=True
            )
            chat.draft = self.main_panel_controller.get_draft()
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _assistant_message_dict(
        self,
        content: list | None = None,
    ) -> dict:
        return {
            "role": "assistant",
            "content": content or [],
            "timestamp": datetime.now().isoformat(),
        }

    def _ensure_turn_assistant_in_store(self) -> dict | None:
        if not self._turn_chat_id:
            return None
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return None
        if not chat.messages or chat.messages[-1].get("role") != "assistant":
            chat.messages.append(self._assistant_message_dict())
        assistant_message = chat.messages[-1]
        if not isinstance(assistant_message.get("content"), list):
            assistant_message["content"] = []
        return assistant_message

    def _append_turn_part_to_store(self, part: dict) -> None:
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return
        assistant_message["content"].append(part)
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _append_turn_reasoning_to_store(self, delta: str) -> None:
        if not delta:
            return
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return
        content = assistant_message["content"]
        if content and content[-1].get("type") == "reasoning":
            content[-1]["text"] = content[-1].get("text", "") + delta
        else:
            content.append({"type": "reasoning", "text": delta})
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _append_turn_delta_to_store(self, delta: str) -> None:
        if not delta:
            return
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return
        content = assistant_message["content"]
        if content and content[-1].get("type") == "final_answer":
            content[-1]["text"] = content[-1].get("text", "") + delta
        else:
            content.append({"type": "final_answer", "text": delta})
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _insert_turn_error_detail_in_store(self, detail: str) -> None:
        if not detail:
            return
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return
        content = assistant_message["content"]
        part = {"type": "error_detail", "text": detail}
        for index, existing in enumerate(content):
            if existing.get("type") == "final_answer":
                content.insert(index, part)
                break
        else:
            content.append(part)
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _turn_final_answer_text_in_store(self) -> str:
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return ""
        for part in reversed(assistant_message["content"]):
            if part.get("type") == "final_answer":
                return part.get("text", "")
        return ""

    def _set_turn_final_answer_in_store(self, content: str) -> None:
        assistant_message = self._ensure_turn_assistant_in_store()
        if assistant_message is None:
            return
        parts = assistant_message["content"]
        for part in reversed(parts):
            if part.get("type") == "final_answer":
                part["text"] = content
                break
        else:
            parts.append({"type": "final_answer", "text": content})
        chat = self.store.get(self._turn_chat_id)
        if chat is None:
            return
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _clear_turn_state(self) -> None:
        self._turn_chat_id = None
        self._turn_tool_calls = []
        self._turn_reasoning = ""
        self.main_panel_controller.set_agent_turn_in_progress(False)
        self.side_panel_controller.set_chat_loading(None)

    def _select_chat(self, chat: Chat) -> None:
        """Load a chat's messages into the main panel."""
        previous_chat_id = self.current_chat_id
        self._loading_conversation = True
        try:
            if previous_chat_id and previous_chat_id != chat.id:
                if self._agent_runner.is_running() and self._turn_chat_id:
                    self._persist_turn_chat(self._turn_chat_id)
                else:
                    self._save_current_chat()

            if self._agent_runner.is_running():
                self.main_panel_controller.detach_inflight_agent_turn()

            self.current_chat_id = chat.id
            self.side_panel_controller.set_active_chat_id(chat.id)
            self.main_panel_controller.load_messages(
                [Message.from_dict(message_data) for message_data in chat.messages]
            )
            self.main_panel_controller.set_draft(chat.draft)

            if (
                self._agent_runner.is_running()
                and self._turn_chat_id == chat.id
            ):
                self.main_panel_controller.reattach_streaming_turn()

            if self._agent_runner.is_running():
                self.main_panel_controller.set_agent_turn_in_progress(True)
            elif not self._agent_runner.is_running():
                self._sync_agent_from_panel()
        finally:
            self._loading_conversation = False

    def _sync_agent_from_panel(self) -> None:
        """Align the backend agent with the visible chat history."""
        self.agent.load_conversation(self.main_panel_controller.get_message_dicts())

    def _set_agent_mode(self, mode: str) -> None:
        self.agent.set_mode(mode)
        self.main_panel_controller.update_mode(mode)

    def _on_mode_change_requested(self, mode: str) -> None:
        if self._agent_runner.is_running():
            self.window.statusBar().showMessage(
                "Wait for the current response to finish before switching mode."
            )
            return
        self._set_agent_mode(mode)
        self.window.statusBar().showMessage(f"Mode: {mode.capitalize()}")

    def _on_special_command_submitted(self, command_text: str) -> None:
        output_messages: list[str] = []
        result = handle_command(
            text=command_text,
            working_dir=self.config.working_dir,
            set_mode=self._set_agent_mode,
            output=output_messages.append,
        )
        if result == CommandResult.NOT_A_COMMAND:
            return
        if output_messages:
            self.main_panel_controller.add_message(
                Message(
                    role="assistant",
                    content=[
                        {
                            "type": "final_answer",
                            "text": "\n".join(output_messages),
                        }
                    ],
                )
            )
        if result == CommandResult.EXIT:
            self._save_current_chat()
            self.window.close()
            return
        self.window.statusBar().showMessage("Ready")

    def _on_agent_turn_requested(self) -> None:
        if self._agent_runner.is_running():
            self.main_panel_controller.cancel_inflight_agent_request()
            return
        self._turn_chat_id = self.current_chat_id
        self._turn_tool_calls = []
        self._turn_reasoning = ""
        self.main_panel_controller.set_agent_turn_in_progress(True)
        self.side_panel_controller.set_chat_loading(self._turn_chat_id)
        self._sync_agent_from_panel()
        self.window.statusBar().showMessage("Thinking...")
        self._agent_runner.start_turn(self.agent)

    def _on_agent_turn_stop_requested(self) -> None:
        if not self._agent_runner.is_running():
            return
        self.window.statusBar().showMessage("Stopping...")
        self._agent_runner.stop_turn()

    def _on_agent_turn_cancelled(self) -> None:
        turn_chat_id = self._turn_chat_id
        if turn_chat_id == self.current_chat_id:
            self.main_panel_controller.finalize_stopped_agent_turn()
        elif turn_chat_id:
            chat = self.store.get(turn_chat_id)
            if chat is not None and chat.messages:
                last_message = chat.messages[-1]
                if last_message.get("role") == "assistant":
                    content = last_message.get("content")
                    if not content:
                        chat.messages.pop()
                chat.updated_at = datetime.now()
                self.store.save(chat)
            self.main_panel_controller.detach_inflight_agent_turn()
        self._clear_turn_state()
        self._sync_agent_from_panel()
        self.window.statusBar().showMessage("Stopped")

    def _on_agent_text_delta(self, delta: str) -> None:
        if not self._turn_chat_id or not delta:
            return
        if self._turn_chat_id == self.current_chat_id:
            self.main_panel_controller.append_agent_text_delta(delta)
        else:
            self._append_turn_delta_to_store(delta)

    def _on_agent_reasoning_delta(self, delta: str) -> None:
        if not self._turn_chat_id or not delta:
            return
        self._turn_reasoning += delta
        if self._turn_chat_id == self.current_chat_id:
            self.main_panel_controller.append_agent_reasoning_delta(delta)
        else:
            self._append_turn_reasoning_to_store(delta)

    def _on_agent_tool_call_started(
        self,
        name: str,
        arguments: str,
        call_id: str,
    ) -> None:
        self._turn_tool_calls.append(
            {
                "id": call_id,
                "name": name,
                "arguments": arguments,
            }
        )
        if self._turn_chat_id != self.current_chat_id:
            self._append_turn_part_to_store(
                {
                    "type": "tool_call",
                    "id": call_id,
                    "name": name,
                    "arguments": arguments,
                }
            )
        if self._turn_chat_id == self.current_chat_id:
            self.main_panel_controller.record_agent_tool_call_started(
                name,
                arguments,
                call_id,
            )
        self.window.statusBar().showMessage(f"Running tool: {name}")

    def _on_agent_tool_result(self, call_id: str, output: str) -> None:
        for tool_call in self._turn_tool_calls:
            if tool_call.get("id") == call_id:
                tool_call["result"] = output
                break
        if self._turn_chat_id != self.current_chat_id:
            self._append_turn_part_to_store(
                {
                    "type": "tool_result",
                    "tool_call_id": call_id,
                    "content": output,
                }
            )
        if self._turn_chat_id == self.current_chat_id:
            self.main_panel_controller.record_agent_tool_result(call_id, output)

    def _on_agent_turn_complete(self, content: str, tool_calls: list) -> None:
        turn_chat_id = self._turn_chat_id
        if turn_chat_id == self.current_chat_id:
            self.main_panel_controller.complete_streaming_agent_turn(
                content,
            )
        else:
            if content:
                self._set_turn_final_answer_in_store(content)
            self.main_panel_controller.detach_inflight_agent_turn()
        self._clear_turn_state()
        self.window.statusBar().showMessage("Ready")

    def _on_agent_error(self, error: str, error_detail: str) -> None:
        turn_chat_id = self._turn_chat_id
        if turn_chat_id == self.current_chat_id:
            self.main_panel_controller.fail_agent_turn(error, error_detail)
        elif turn_chat_id:
            chat = self.store.get(turn_chat_id)
            if chat is not None:
                detail = (error_detail or error).strip()
                if detail:
                    self._insert_turn_error_detail_in_store(detail)
                partial = self._turn_final_answer_text_in_store().strip()
                summary = (
                    f"An error occurred: {error}. "
                    "See stack trace above for details."
                )
                final_text = f"{partial}\n\n{summary}" if partial else summary
                self._set_turn_final_answer_in_store(final_text)
            self.main_panel_controller.detach_inflight_agent_turn()
        else:
            self.main_panel_controller.fail_agent_turn(error, error_detail)
        self._clear_turn_state()
        self.window.statusBar().showMessage(f"Error: {error}")

    def _on_messages_changed(self) -> None:
        self._save_current_chat()

    def _on_draft_changed(self) -> None:
        self._save_current_chat()

    def on_chat_selected(self, chat: Chat):
        if chat.id == self.current_chat_id:
            return
        self._select_chat(chat)

    def on_chat_created(self, chat: Chat):
        self._save_current_chat()
        self.store.add(chat)
        self.update_side_panel()
        self._select_chat(chat)
        QTimer.singleShot(0, lambda: self.side_panel_controller.start_inline_rename(chat))

    def on_chat_renamed(self, chat: Chat):
        self.store.save(chat)
        self.update_side_panel()

    def on_chat_deleted(self, chat: Chat):
        was_current = chat.id == self.current_chat_id
        self.store.remove(chat)
        self.update_side_panel()

        if not was_current:
            return

        remaining = self.store.all()
        if remaining:
            self._select_chat(remaining[0])
        else:
            self._select_chat(self._create_default_chat())

    def on_theme_toggle(self):
        self.gui_config.theme = "dark" if self.gui_config.theme == "light" else "light"

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.gui_config.theme))

        self.main_panel_controller.apply_theme(self.gui_config.theme)
        self.side_panel_controller.apply_theme(self.gui_config.theme)
