"""
Main GUI Window for Bookworm

This module implements the main application window that integrates the thread panel
and chat panel components.
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, 
    QVBoxLayout, QSplitter, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from .thread_panel import ThreadPanel, Thread
from .chat_panel import ChatPanel
from .config import GUIConfig
from ..config import Config

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
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.gui_config.window_title)
        self.setMinimumSize(self.gui_config.window_width, self.gui_config.window_height)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create thread panel
        self.thread_panel = ThreadPanel(self.gui_config)
        self.thread_panel.on_thread_selected.connect(self.on_thread_selected)
        
        # Create chat panel
        self.chat_panel = ChatPanel(self.gui_config)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.thread_panel)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([self.gui_config.thread_panel_width, 
                          self.width() - self.gui_config.thread_panel_width])
        
        main_layout.addWidget(splitter)
        
        # Set up status bar
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
            from .chat_panel import Message
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
        """Handle thread selection."""
        # Clear current chat
        self.chat_panel.messages.clear()
        self.chat_panel.message_layout.removeWidget(
            self.chat_panel.message_layout.itemAt(0).widget()
        )
        
        # Load thread messages
        for message_data in thread.messages:
            message = ChatPanel.Message.from_dict(message_data)
            self.chat_panel.add_message(message)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # TODO: Save thread state before closing
        event.accept()