"""
BookWorm GUI - Graphical User Interface for Bookworm AI Agent

This package provides a modern GUI interface for the Bookworm AI coding assistant,
replacing the terminal-based interface with a user-friendly graphical application
using PySide6.
"""

__version__ = "0.1.0"
__author__ = "BookWorm Engineer"

from .main_window import BookwormGUI
from .thread_panel import ThreadPanel, Thread
from .chat_panel import ChatPanel, Message
from .config import GUIConfig
from .themes import get_colors, build_stylesheet, COLOR_SCHEMES

__all__ = [
    "BookwormGUI",
    "ThreadPanel",
    "Thread",
    "ChatPanel",
    "Message",
    "GUIConfig",
    "get_colors",
    "build_stylesheet",
    "COLOR_SCHEMES",
]