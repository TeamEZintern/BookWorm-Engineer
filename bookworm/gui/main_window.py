"""
Main GUI Window for Bookworm

This module implements the main application window that integrates the thread panel
and chat panel components.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QSplitter, QPushButton, QLabel
)
from PySide6.QtCore import Qt

from .thread_panel import ThreadPanel, Thread
from .chat_panel import ChatPanel, Message
from .config import GUIConfig
from ..config import Config
from .themes import build_stylesheet, get_colors

class BookwormGUI(QMainWindow):
    """
    Main GUI window for Bookworm.
    
    This window integrates the thread panel and chat panel components,
    providing a complete graphical interface for the Bookworm AI agent.
    """
    
    def __init__(self, config: Config, gui_config: GUIConfig):
        super().__init__()
        self.config = config
        self.gui_config = gui_config
        self.threads: List[Thread] = []
        self.current_thread_id: Optional[str] = None

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(gui_config.theme))

        self.setup_ui()
        self.load_initial_data()

    def _theme_icon(self) -> str:
        return "🌞" if self.gui_config.theme == "light" else "🌚"

    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.gui_config.window_title)
        self.setMinimumSize(self.gui_config.window_width, self.gui_config.window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header bar
        header_colors = get_colors(self.gui_config.theme)
        header_bar = QWidget()
        header_bar.setStyleSheet(f"background-color: {header_colors['bg_tertiary']}; color: {header_colors['text_primary']};")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(12, 4, 8, 4)

        title_label = QLabel("BookWorm Engineer")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.theme_btn = QPushButton(self._theme_icon())
        self.theme_btn.setFixedSize(44, 28)
        self.theme_btn.setToolTip(f"Switch to {'dark' if self.gui_config.theme == 'light' else 'light'} mode")
        self.theme_btn.clicked.connect(self.on_theme_toggle)
        self.theme_btn.setStyleSheet("border: 1px solid " + header_colors['border'] + "; border-radius: 4px; background: transparent; font-size: 16px; padding: 0px;")
        header_layout.addWidget(self.theme_btn)

        root_layout.addWidget(header_bar)

        # Body with splitter
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.thread_panel = ThreadPanel(self.gui_config)
        self.thread_panel.on_thread_selected.connect(self.on_thread_selected)

        self.chat_panel = ChatPanel(self.gui_config)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.thread_panel)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([self.gui_config.thread_panel_width,
                          self.width() - self.gui_config.thread_panel_width])

        body_layout.addWidget(splitter)
        root_layout.addLayout(body_layout, 1)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def load_initial_data(self):
        """Load initial data for the GUI."""
        # Load threads from storage
        self.load_threads()
        
        # Create a default thread if none exist
        if not self.threads:
            import uuid
            from datetime import datetime
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
            self.threads.append(default_thread)
            self.update_thread_panel()
        
        # Select the first thread
        if self.threads:
            self.chat_panel.add_message(
                Message.from_dict(self.threads[0].messages[0])
            )
    
    def load_threads(self):
        """Load threads from storage."""
        # TODO: Implement thread loading from storage
        # For now, start with empty threads
        self.threads = []
    
    def update_thread_panel(self):
        """Update the thread panel with current threads."""
        self.thread_panel.update_thread_list(self.threads)
    
    def on_thread_selected(self, thread: Thread):
        if thread.id == self.current_thread_id:
            return
        # TODO: Save current thread state before switching
        self.current_thread_id = thread.id
        self.chat_panel.clear_messages()
        for message_data in thread.messages:
            message = Message.from_dict(message_data)
            self.chat_panel.add_message(message)
    
    def on_theme_toggle(self):
        self.gui_config.theme = "dark" if self.gui_config.theme == "light" else "light"
        colors = get_colors(self.gui_config.theme)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.gui_config.theme))

        self.chat_panel.apply_theme(self.gui_config.theme)

        self.theme_btn.setText(self._theme_icon())
        self.theme_btn.setToolTip(f"Switch to {'dark' if self.gui_config.theme == 'light' else 'light'} mode")
        header_bar = self.centralWidget().layout().itemAt(0).widget()
        header_bar.setStyleSheet(f"background-color: {colors['bg_tertiary']}; color: {colors['text_primary']};")
        self.theme_btn.setStyleSheet("border: 1px solid " + colors['border'] + "; border-radius: 4px; background: transparent; font-size: 16px; padding: 0px;")

    def closeEvent(self, event):
        """Handle window close event."""
        # TODO: Save thread state before closing
        event.accept()