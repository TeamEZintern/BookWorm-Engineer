"""
BookWorm GUI Controllers

Controllers own their generated views, wire signals via ``findChild()``, and
hold the GUI behaviour previously embedded in the monolithic panel classes.
"""

from .app_controller import AppController
from .chat_controller import ChatController
from .thread_controller import ThreadController

__all__ = [
    "AppController",
    "ChatController",
    "ThreadController",
]
