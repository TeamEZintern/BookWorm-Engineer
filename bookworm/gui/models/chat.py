"""
Chat Model

Represents a chat and its message history.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

REQUIRED_CHAT_KEYS = {"id", "name", "created_at", "updated_at", "messages"}
REQUIRED_MESSAGE_KEYS = {"role", "content", "timestamp"}
VALID_ROLES = {"user", "assistant", "system"}


def default_chat_name(when: Optional[datetime] = None) -> str:
    """Return a default chat name from its creation time.

    Example: ``New Chat 11:30 AM 22/6/2026``
    """
    when = when or datetime.now()
    time_part = when.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    date_part = f"{when.day}/{when.month}/{when.year}"
    return f"New Chat {time_part} {date_part}"


def validate_message_data(data: Any) -> None:
    """Validate a single message object from a chat JSON file."""
    if not isinstance(data, dict):
        raise ValueError("message must be an object")
    missing = REQUIRED_MESSAGE_KEYS - data.keys()
    if missing:
        raise ValueError(f"message missing required keys: {sorted(missing)}")
    if data["role"] not in VALID_ROLES:
        raise ValueError(f"invalid message role: {data['role']!r}")
    if not isinstance(data["content"], str):
        raise ValueError("message content must be a string")
    if not isinstance(data["timestamp"], str):
        raise ValueError("message timestamp must be a string")
    tool_calls = data.get("tool_calls", [])
    if tool_calls is not None and not isinstance(tool_calls, list):
        raise ValueError("message tool_calls must be a list")


def validate_chat_data(data: Any) -> None:
    """Validate a chat object loaded from JSON."""
    if not isinstance(data, dict):
        raise ValueError("chat must be an object")
    missing = REQUIRED_CHAT_KEYS - data.keys()
    if missing:
        raise ValueError(f"chat missing required keys: {sorted(missing)}")
    if not isinstance(data["id"], str) or not data["id"].strip():
        raise ValueError("chat id must be a non-empty string")
    if not isinstance(data["name"], str):
        raise ValueError("chat name must be a string")
    if not isinstance(data["created_at"], str):
        raise ValueError("chat created_at must be a string")
    if not isinstance(data["updated_at"], str):
        raise ValueError("chat updated_at must be a string")
    if not isinstance(data["messages"], list):
        raise ValueError("chat messages must be a list")
    for message in data["messages"]:
        validate_message_data(message)


class Chat:
    """Represents a chat."""

    def __init__(self, chat_id: str, name: str, created_at: datetime,
                 updated_at: datetime, messages: Optional[List[Dict[str, Any]]] = None):
        self.id = chat_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at
        self.messages = messages or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert chat to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chat":
        """Create chat from dictionary."""
        validate_chat_data(data)
        return cls(
            chat_id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data.get("messages", []),
        )
