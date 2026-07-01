"""
BookWorm GUI Models

Data models for the GUI layer: chats, messages, and the in-memory store.
"""

from .message import Message
from .chat import (
    Chat,
    default_chat_name,
    get_active_attempt_content,
    new_assistant_message_dict,
    validate_chat_data,
    validate_message_data,
)
from .chat_store import ChatStore

__all__ = [
    "Message",
    "Chat",
    "ChatStore",
    "default_chat_name",
    "get_active_attempt_content",
    "new_assistant_message_dict",
    "validate_chat_data",
    "validate_message_data",
]
