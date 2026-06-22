"""
BookWorm GUI Models

Data models for the GUI layer: threads, messages, and the in-memory store.
"""

from .message import Message
from .thread import Thread
from .thread_store import ThreadStore

__all__ = [
    "Message",
    "Thread",
    "ThreadStore",
]
