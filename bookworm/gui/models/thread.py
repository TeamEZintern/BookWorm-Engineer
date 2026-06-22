"""
Thread Model

Represents a conversation thread and its message history.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class Thread:
    """Represents a conversation thread."""

    def __init__(self, thread_id: str, name: str, created_at: datetime,
                 updated_at: datetime, messages: Optional[List[Dict[str, Any]]] = None):
        self.id = thread_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at
        self.messages = messages or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thread':
        """Create thread from dictionary."""
        return cls(
            thread_id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data.get("messages", [])
        )
