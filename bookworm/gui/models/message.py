"""
Message Model

Represents a single message within a chat.
"""

from typing import Dict, Any, Optional
from datetime import datetime

Content = str | list[dict[str, Any]]


class Message:
    """Represents a message in the chat."""

    def __init__(
        self,
        role: str,
        content: Content,
        timestamp: Optional[datetime] = None,
    ):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()

    @classmethod
    def assistant(cls, timestamp: Optional[datetime] = None) -> "Message":
        """Create an assistant message whose content is ordered response parts."""
        return cls(role="assistant", content=[], timestamp=timestamp)

    @property
    def parts(self) -> list[dict[str, Any]]:
        """Return assistant content parts, or an empty list for plain text messages."""
        return self.content if isinstance(self.content, list) else []

    @property
    def text(self) -> str:
        """Plain display/API text for user messages or final assistant answers."""
        if isinstance(self.content, str):
            return self.content
        return "".join(
            part.get("text", "")
            for part in self.content
            if part.get("type") == "final_answer"
        )

    def append_reasoning_delta(self, delta: str) -> None:
        if not isinstance(self.content, list):
            self.content = []
        if self.content and self.content[-1].get("type") == "reasoning":
            self.content[-1]["text"] = self.content[-1].get("text", "") + delta
            return
        self.content.append({"type": "reasoning", "text": delta})

    def append_tool_call(self, call_id: str, name: str, arguments: str) -> None:
        if not isinstance(self.content, list):
            self.content = []
        self.content.append(
            {
                "type": "tool_call",
                "id": call_id,
                "name": name,
                "arguments": arguments,
            }
        )

    def append_tool_result(self, call_id: str, output: str) -> None:
        if not isinstance(self.content, list):
            self.content = []
        self.content.append(
            {
                "type": "tool_result",
                "tool_call_id": call_id,
                "content": output,
            }
        )

    def append_error_detail(self, text: str) -> None:
        """Insert stack trace / error logs before the final answer, if any."""
        if not isinstance(self.content, list):
            self.content = []
        part = {"type": "error_detail", "text": text}
        for index, existing in enumerate(self.content):
            if existing.get("type") == "final_answer":
                self.content.insert(index, part)
                return
        self.content.append(part)

    def append_final_answer_delta(self, delta: str) -> None:
        if not isinstance(self.content, list):
            self.content = []
        if self.content and self.content[-1].get("type") == "final_answer":
            self.content[-1]["text"] = self.content[-1].get("text", "") + delta
            return
        self.content.append({"type": "final_answer", "text": delta})

    def set_final_answer(self, text: str) -> None:
        if not isinstance(self.content, list):
            self.content = []
        for part in reversed(self.content):
            if part.get("type") == "final_answer":
                part["text"] = text
                return
        self.content.append({"type": "final_answer", "text": text})

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
