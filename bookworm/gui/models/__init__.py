"""
BookWorm GUI Models

Data models for the GUI layer: threads, messages, and the in-memory store.
"""

from .message import Message
from .thread import (
    Thread,
    default_thread_name,
    validate_message_data,
    validate_thread_data,
)
from .thread_store import ThreadStore

__all__ = [
    "Message",
    "Thread",
    "ThreadStore",
    "default_thread_name",
    "validate_thread_data",
    "validate_message_data",
]
