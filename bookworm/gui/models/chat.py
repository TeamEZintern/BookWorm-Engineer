"""
Chat Model

Represents a chat and its message history.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

DRAFT_KEY = "draft"
REQUIRED_CHAT_KEYS = {"id", "name", "created_at", "updated_at", "messages"}
REQUIRED_USER_MESSAGE_KEYS = {"role", "content", "timestamp"}
REQUIRED_ASSISTANT_MESSAGE_KEYS = {"role", "num_attempts", "active_attempt", "attempts"}
VALID_ROLES = {"user", "assistant", "system"}
ASSISTANT_PART_TYPES = {"reasoning", "tool_call", "tool_result", "final_answer", "error_detail"}


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
    role = data.get("role")
    if role not in VALID_ROLES:
        raise ValueError(f"invalid message role: {role!r}")
    if role == "user":
        _validate_user_message_data(data)
    elif role == "assistant":
        _validate_assistant_message_data(data)


def _validate_user_message_data(data: dict[str, Any]) -> None:
    missing = REQUIRED_USER_MESSAGE_KEYS - data.keys()
    if missing:
        raise ValueError(f"message missing required keys: {sorted(missing)}")
    if not isinstance(data["timestamp"], str):
        raise ValueError("message timestamp must be a string")
    if not isinstance(data["content"], str):
        raise ValueError("user message content must be a string")


def _validate_assistant_message_data(data: dict[str, Any]) -> None:
    missing = REQUIRED_ASSISTANT_MESSAGE_KEYS - data.keys()
    if missing:
        raise ValueError(f"message missing required keys: {sorted(missing)}")
    attempts = data["attempts"]
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("assistant message attempts must be a non-empty list")
    if not isinstance(data["num_attempts"], int) or data["num_attempts"] != len(attempts):
        raise ValueError("assistant num_attempts must match attempts length")
    if not isinstance(data["active_attempt"], int):
        raise ValueError("assistant active_attempt must be an integer")
    if not any(item.get("index") == data["active_attempt"] for item in attempts):
        raise ValueError("assistant active_attempt must reference an existing attempt")
    for attempt in attempts:
        validate_assistant_attempt(attempt)


def validate_assistant_attempt(attempt: Any) -> None:
    if not isinstance(attempt, dict):
        raise ValueError("assistant attempt must be an object")
    for key in ("index", "content", "timestamp"):
        if key not in attempt:
            raise ValueError(f"assistant attempt missing required key: {key}")
    if not isinstance(attempt["index"], int):
        raise ValueError("assistant attempt index must be an integer")
    if not isinstance(attempt["timestamp"], str):
        raise ValueError("assistant attempt timestamp must be a string")
    if not isinstance(attempt["content"], list):
        raise ValueError("assistant attempt content must be a list")
    for part in attempt["content"]:
        validate_assistant_part(part)


def validate_assistant_part(part: Any) -> None:
    """Validate one ordered assistant response part."""
    if not isinstance(part, dict):
        raise ValueError("assistant content part must be an object")
    part_type = part.get("type")
    if part_type not in ASSISTANT_PART_TYPES:
        raise ValueError(f"invalid assistant content part type: {part_type!r}")
    if part_type in {"reasoning", "final_answer", "error_detail"}:
        if not isinstance(part.get("text"), str):
            raise ValueError(f"{part_type} part text must be a string")
        return
    if part_type == "tool_call":
        for key in ("id", "name", "arguments"):
            if not isinstance(part.get(key), str):
                raise ValueError(f"tool_call part {key} must be a string")
        return
    if not isinstance(part.get("tool_call_id"), str):
        raise ValueError("tool_result part tool_call_id must be a string")
    if not isinstance(part.get("content"), str):
        raise ValueError("tool_result part content must be a string")


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
    if DRAFT_KEY in data and not isinstance(data[DRAFT_KEY], str):
        raise ValueError("chat draft must be a string")
    for message in data["messages"]:
        validate_message_data(message)


def get_active_attempt_content(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the content list for an assistant message's active attempt."""
    if message.get("role") != "assistant":
        raise ValueError("expected assistant message")
    active = message["active_attempt"]
    for attempt in message["attempts"]:
        if attempt.get("index") == active:
            return attempt["content"]
    return message["attempts"][-1]["content"]


def new_assistant_message_dict(
    content: Optional[list[dict[str, Any]]] = None,
    *,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Build a single-attempt assistant message dict for persistence."""
    ts = timestamp or datetime.now().isoformat()
    return {
        "role": "assistant",
        "num_attempts": 1,
        "active_attempt": 1,
        "attempts": [
            {
                "index": 1,
                "content": content or [],
                "timestamp": ts,
            }
        ],
    }


class Chat:
    """Represents a chat."""

    def __init__(self, chat_id: str, name: str, created_at: datetime,
                 updated_at: datetime, messages: Optional[List[Dict[str, Any]]] = None,
                 draft: str = ""):
        self.id = chat_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at
        self.messages = messages or []
        self.draft = draft

    def to_dict(self) -> Dict[str, Any]:
        """Convert chat to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            DRAFT_KEY: self.draft,
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
            draft=data.get(DRAFT_KEY, ""),
        )
