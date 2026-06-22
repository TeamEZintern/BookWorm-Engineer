"""
BookWorm GUI - Graphical User Interface for Bookworm AI Agent

This package provides a modern GUI interface for the Bookworm AI coding assistant,
replacing the terminal-based interface with a user-friendly graphical application
using PySide6.

The GUI follows an MVC layout:
- ``models/``      - data models (Thread, Message, ThreadStore)
- ``views/``       - Qt Designer ``.ui`` files + generated ``ui_*.py``
- ``controllers/`` - behaviour, wired to views via ``findChild()``
"""

__version__ = "0.1.0"
__author__ = "BookWorm Engineer"

from .config import GUIConfig
from .controllers import AppController, ChatController, ThreadController
from .models import Message, Thread, ThreadStore
from .themes import get_colors, build_stylesheet, COLOR_SCHEMES

__all__ = [
    "AppController",
    "ChatController",
    "ThreadController",
    "Message",
    "Thread",
    "ThreadStore",
    "GUIConfig",
    "get_colors",
    "build_stylesheet",
    "COLOR_SCHEMES",
]
