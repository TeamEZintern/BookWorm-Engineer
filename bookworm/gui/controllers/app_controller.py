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
            "content": (
                "Welcome to Bookworm GUI! This is a graphical interface for the "
                "Bookworm AI coding assistant. You can create, rename, and delete "
                "chats, and chat with the agent."
            ),
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
        chat.messages = self.main_panel_controller.get_message_dicts()
        chat.draft = self.main_panel_controller.get_draft()
        chat.updated_at = datetime.now()
        self.store.save(chat)

    def _select_chat(self, chat: Chat) -> None:
        """Load a chat's messages into the main panel."""
        self._loading_conversation = True
        try:
            self.current_chat_id = chat.id
            self.side_panel_controller.set_active_chat_id(chat.id)
            self.main_panel_controller.clear_messages()
            for message_data in chat.messages:
                self.main_panel_controller.add_message(Message.from_dict(message_data))
            self.main_panel_controller.set_draft(chat.draft)
        finally:
            self._loading_conversation = False

    def _on_messages_changed(self) -> None:
        self._save_current_chat()

    def _on_draft_changed(self) -> None:
        self._save_current_chat()

    def on_chat_selected(self, chat: Chat):
        if chat.id == self.current_chat_id:
            return
        self._save_current_chat()
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
