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
from ..models import Message, Thread, ThreadStore
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
        self.store = ThreadStore()
        self.current_thread_id = None

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
        self.thread_controller.theme_toggle_requested.connect(self.on_theme_toggle)

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

    def load_initial_data(self):
        """Load initial data for the GUI."""
        self.store.load()

        if self.store.is_empty():
            default_thread = Thread(
                thread_id=str(uuid.uuid4()),
                name="New Thread",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[
                    {
                        "role": "assistant",
                        "content": "Welcome to Bookworm GUI! This is a graphical interface for the Bookworm AI coding assistant. You can create, rename, and delete threads, and chat with the agent.",
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            )
            self.store.add(default_thread)
            self.update_thread_panel()

        threads = self.store.all()
        if threads:
            self.current_thread_id = threads[0].id
            self.thread_controller.set_active_thread_id(self.current_thread_id)
            for message_data in threads[0].messages:
                self.chat_controller.add_message(Message.from_dict(message_data))

    def update_thread_panel(self):
        """Update the thread panel with current threads."""
        self.thread_controller.update_thread_list(self.store.all())

    def on_thread_selected(self, thread: Thread):
        if thread.id == self.current_thread_id:
            return
        # TODO: Save current thread state before switching
        self.current_thread_id = thread.id
        self.thread_controller.set_active_thread_id(thread.id)
        self.chat_controller.clear_messages()
        for message_data in thread.messages:
            message = Message.from_dict(message_data)
            self.chat_controller.add_message(message)

    def on_theme_toggle(self):
        self.gui_config.theme = "dark" if self.gui_config.theme == "light" else "light"

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.gui_config.theme))

        self.chat_controller.apply_theme(self.gui_config.theme)
        self.thread_controller.apply_theme(self.gui_config.theme)
