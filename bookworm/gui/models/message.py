"""
Message Model

Represents a single message within a conversation thread.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class Message:
    """Represents a message in the chat."""

    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None,
                 tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.tool_calls = tool_calls or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tool_calls=data.get("tool_calls", [])
        )
