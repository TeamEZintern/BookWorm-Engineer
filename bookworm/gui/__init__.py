"""
BookWorm GUI - Graphical User Interface for Bookworm AI Agent

This package provides a modern GUI interface for the Bookworm AI coding assistant,
replacing the terminal-based interface with a user-friendly graphical application
using PySide6.
"""

__version__ = "0.1.0"
__author__ = "BookWorm Engineer"

from .main_window import BookwormGUI
from .thread_panel import ThreadPanel
from .chat_panel import ChatPanel
from .config import GUIConfig

__all__ = [
    "BookwormGUI",
    "ThreadPanel", 
    "ChatPanel",
    "GUIConfig"
]