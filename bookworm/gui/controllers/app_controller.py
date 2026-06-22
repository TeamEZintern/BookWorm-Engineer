"""
App Controller

Top-level controller for the BookWorm GUI. Owns the main window view
(``ui_main_window``), instantiates the thread and chat controllers, injects
their widgets into the splitter, and coordinates loading a thread's
conversation into the chat panel.
"""

import uuid
from datetime import datetime

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from ..config import GUIConfig
from ..models import Message, Thread, ThreadStore, default_thread_name
from ..themes import build_stylesheet
from ..views.window.ui_main_window import Ui_MainWindow
from .chat_controller import ChatController
from .thread_controller import ThreadController


class AppController(QObject):
    """
    Main controller wiring together the window, thread panel, and chat panel.

    Exposes ``self.window`` (a ``QMainWindow``) for the CLI to ``show()``.
    """

    def __init__(self, config, gui_config: GUIConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.gui_config = gui_config
        threads_dir = config.working_dir / ".bookworm" / "threads"
        self.store = ThreadStore(threads_dir)
        self.current_thread_id = None
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

        self.thread_controller = ThreadController(gui_config)
        self.chat_controller = ChatController(gui_config)
        self.thread_controller.thread_selected.connect(self.on_thread_selected)
        self.thread_controller.thread_created.connect(self.on_thread_created)
        self.thread_controller.thread_renamed.connect(self.on_thread_renamed)
        self.thread_controller.thread_deleted.connect(self.on_thread_deleted)
        self.thread_controller.theme_toggle_requested.connect(self.on_theme_toggle)
        self.chat_controller.messages_changed.connect(self._on_messages_changed)

        self.splitter.addWidget(self.thread_controller.widget)
        self.splitter.addWidget(self.chat_controller.widget)
        self.splitter.setSizes([
            gui_config.thread_panel_width,
            self.window.width() - gui_config.thread_panel_width,
        ])

        self.window.statusBar().showMessage("Ready")

        self.load_initial_data()
        self._apply_theme_to_controllers()

    def _apply_theme_to_controllers(self):
        self.thread_controller.apply_theme(self.gui_config.theme)

    def _default_welcome_message(self) -> dict:
        return {
            "role": "assistant",
            "content": (
                "Welcome to Bookworm GUI! This is a graphical interface for the "
                "Bookworm AI coding assistant. You can create, rename, and delete "
                "threads, and chat with the agent."
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def _create_default_thread(self) -> Thread:
        now = datetime.now()
        thread = Thread(
            thread_id=str(uuid.uuid4()),
            name=default_thread_name(now),
            created_at=now,
            updated_at=now,
            messages=[self._default_welcome_message()],
        )
        self.store.add(thread)
        return thread

    def load_initial_data(self):
        """Load threads from disk and show the first conversation."""
        self.store.load()

        if self.store.is_empty():
            self._create_default_thread()

        self.update_thread_panel()
        threads = self.store.all()
        if threads:
            self._select_thread(threads[0])

    def update_thread_panel(self):
        """Update the thread panel with current threads."""
        self.thread_controller.update_thread_list(self.store.all())

    def _save_current_thread(self) -> None:
        """Persist the active chat into the current thread JSON file."""
        if self._loading_conversation or not self.current_thread_id:
            return
        thread = self.store.get(self.current_thread_id)
        if thread is None:
            return
        thread.messages = self.chat_controller.get_message_dicts()
        thread.updated_at = datetime.now()
        self.store.save(thread)

    def _select_thread(self, thread: Thread) -> None:
        """Load a thread's messages into the chat panel."""
        self._loading_conversation = True
        try:
            self.current_thread_id = thread.id
            self.thread_controller.set_active_thread_id(thread.id)
            self.chat_controller.clear_messages()
            for message_data in thread.messages:
                self.chat_controller.add_message(Message.from_dict(message_data))
        finally:
            self._loading_conversation = False

    def _on_messages_changed(self) -> None:
        self._save_current_thread()

    def on_thread_selected(self, thread: Thread):
        if thread.id == self.current_thread_id:
            return
        self._save_current_thread()
        self._select_thread(thread)

    def on_thread_created(self, thread: Thread):
        self._save_current_thread()
        self.store.add(thread)
        self.update_thread_panel()
        self._select_thread(thread)

    def on_thread_renamed(self, thread: Thread):
        self.store.save(thread)
        self.update_thread_panel()

    def on_thread_deleted(self, thread: Thread):
        was_current = thread.id == self.current_thread_id
        self.store.remove(thread)
        self.update_thread_panel()

        if not was_current:
            return

        remaining = self.store.all()
        if remaining:
            self._select_thread(remaining[0])
        else:
            self._select_thread(self._create_default_thread())

    def on_theme_toggle(self):
        self.gui_config.theme = "dark" if self.gui_config.theme == "light" else "light"

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.gui_config.theme))

        self.chat_controller.apply_theme(self.gui_config.theme)
        self.thread_controller.apply_theme(self.gui_config.theme)
