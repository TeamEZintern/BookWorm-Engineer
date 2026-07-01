"""
Message Model

Represents a single message within a chat.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

Attempt = dict[str, Any]


class Message:
    """Represents a message in the chat."""

    def __init__(
        self,
        role: str,
        content: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        *,
        attempts: Optional[List[Attempt]] = None,
        active_attempt: int = 1,
    ):
        self.role = role  # "user" or "assistant"
        if role == "user":
            if content is None:
                raise ValueError("user messages require string content")
            self.content = content
            self._timestamp = timestamp or datetime.now()
            self.attempts: List[Attempt] = []
            self.active_attempt = 1
        elif role == "assistant":
            self.content = None
            self._timestamp = None
            self.attempts = attempts or []
            self.active_attempt = active_attempt
        else:
            raise ValueError(f"unsupported message role: {role!r}")

    @classmethod
    def assistant(cls, timestamp: Optional[datetime] = None) -> "Message":
        """Create an assistant message with one empty attempt for streaming."""
        message = cls(role="assistant", attempts=[], active_attempt=1)
        message.begin_new_attempt(timestamp=timestamp)
        return message

    @classmethod
    def assistant_from_attempts(
        cls,
        attempts: List[Attempt],
        active_attempt: int,
    ) -> "Message":
        return cls(
            role="assistant",
            attempts=deepcopy(attempts),
            active_attempt=active_attempt,
        )

    @property
    def timestamp(self) -> datetime:
        if self.role == "user":
            return self._timestamp
        attempt = self._get_active_attempt()
        if attempt is None:
            return datetime.now()
        ts = attempt.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        return datetime.fromisoformat(ts)

    @property
    def num_attempts(self) -> int:
        return len(self.attempts)

    @property
    def parts(self) -> list[dict[str, Any]]:
        """Return the active attempt's content parts."""
        attempt = self._get_active_attempt()
        if attempt is None:
            return []
        content = attempt.get("content", [])
        return content if isinstance(content, list) else []

    @property
    def text(self) -> str:
        """Plain display/API text for user messages or the active final answer."""
        if self.role == "user":
            return self.content or ""
        return "".join(
            part.get("text", "")
            for part in self.parts
            if part.get("type") == "final_answer"
        )

    def _get_active_attempt(self) -> Optional[Attempt]:
        for attempt in self.attempts:
            if attempt.get("index") == self.active_attempt:
                return attempt
        return self.attempts[-1] if self.attempts else None

    def _active_content(self) -> list[dict[str, Any]]:
        attempt = self._get_active_attempt()
        if attempt is None:
            return []
        content = attempt.setdefault("content", [])
        if not isinstance(content, list):
            content = []
            attempt["content"] = content
        return content

    def begin_new_attempt(self, timestamp: Optional[datetime] = None) -> Attempt:
        """Append an empty attempt and make it active (used for send/redo)."""
        index = len(self.attempts) + 1
        attempt: Attempt = {
            "index": index,
            "content": [],
            "timestamp": timestamp or datetime.now(),
        }
        self.attempts.append(attempt)
        self.active_attempt = index
        return attempt

    def set_active_attempt(self, index: int) -> None:
        if not any(attempt.get("index") == index for attempt in self.attempts):
            raise ValueError(f"attempt {index} does not exist")
        self.active_attempt = index

    def discard_empty_active_attempt(self) -> bool:
        """Remove the active attempt if it has no content; return True if removed."""
        attempt = self._get_active_attempt()
        if attempt is None or attempt.get("content"):
            return False
        self.attempts = [
            item for item in self.attempts if item.get("index") != self.active_attempt
        ]
        if not self.attempts:
            return True
        self.active_attempt = self.attempts[-1]["index"]
        return False

    def append_reasoning_delta(self, delta: str) -> None:
        content = self._active_content()
        if content and content[-1].get("type") == "reasoning":
            content[-1]["text"] = content[-1].get("text", "") + delta
            return
        content.append({"type": "reasoning", "text": delta})

    def append_tool_call(self, call_id: str, name: str, arguments: str) -> None:
        self._active_content().append(
            {
                "type": "tool_call",
                "id": call_id,
                "name": name,
                "arguments": arguments,
            }
        )

    def append_tool_result(self, call_id: str, output: str) -> None:
        self._active_content().append(
            {
                "type": "tool_result",
                "tool_call_id": call_id,
                "content": output,
            }
        )

    def append_error_detail(self, text: str) -> None:
        """Insert stack trace / error logs before the final answer, if any."""
        content = self._active_content()
        part = {"type": "error_detail", "text": text}
        for index, existing in enumerate(content):
            if existing.get("type") == "final_answer":
                content.insert(index, part)
                return
        content.append(part)

    def append_final_answer_delta(self, delta: str) -> None:
        content = self._active_content()
        if content and content[-1].get("type") == "final_answer":
            content[-1]["text"] = content[-1].get("text", "") + delta
            return
        content.append({"type": "final_answer", "text": delta})

    def set_final_answer(self, text: str) -> None:
        content = self._active_content()
        for part in reversed(content):
            if part.get("type") == "final_answer":
                part["text"] = text
                return
        content.append({"type": "final_answer", "text": text})

    def to_dict(self) -> Dict[str, Any]:
        if self.role == "user":
            return {
                "role": "user",
                "content": self.content,
                "timestamp": self._timestamp.isoformat(),
            }
        return {
            "role": "assistant",
            "num_attempts": len(self.attempts),
            "active_attempt": self.active_attempt,
            "attempts": [self._attempt_to_dict(attempt) for attempt in self.attempts],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        role = data["role"]
        if role == "user":
            return cls(
                role="user",
                content=data["content"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        attempts = [cls._attempt_from_dict(item) for item in data["attempts"]]
        return cls(
            role="assistant",
            attempts=attempts,
            active_attempt=data["active_attempt"],
        )

    @classmethod
    def attempt_snapshot_dict(cls, attempt: Attempt) -> Dict[str, Any]:
        """Serialize one attempt as a single-attempt assistant message for the agent."""
        return {
            "role": "assistant",
            "num_attempts": 1,
            "active_attempt": 1,
            "attempts": [cls._attempt_to_dict(attempt)],
        }

    @staticmethod
    def _attempt_to_dict(attempt: Attempt) -> Dict[str, Any]:
        ts = attempt.get("timestamp", datetime.now())
        if isinstance(ts, datetime):
            ts = ts.isoformat()
        return {
            "index": attempt["index"],
            "content": deepcopy(attempt.get("content", [])),
            "timestamp": ts,
        }

    @staticmethod
    def _attempt_from_dict(data: Dict[str, Any]) -> Attempt:
        return {
            "index": data["index"],
            "content": deepcopy(data.get("content", [])),
            "timestamp": datetime.fromisoformat(data["timestamp"]),
        }
