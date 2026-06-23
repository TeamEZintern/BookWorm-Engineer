"""
Chat Store

Loads and saves chats as JSON files under ``.bookworm/chats/``.
Each chat is stored as ``<chat_id>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .chat import Chat


class ChatStore:
    """In-memory chat list backed by JSON files on disk."""

    def __init__(self, chats_dir: Path, chats: Optional[List[Chat]] = None):
        self.chats_dir = chats_dir
        self.chats: List[Chat] = chats or []

    def _path_for(self, chat_id: str) -> Path:
        return self.chats_dir / f"{chat_id}.json"

    def load(self) -> List[Chat]:
        """Load all chats from ``.bookworm/chats/``."""
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        loaded: List[Chat] = []

        for path in sorted(self.chats_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                loaded.append(Chat.from_dict(data))
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                continue

        self.chats = loaded
        return self.chats

    def save(self, chat: Chat) -> None:
        """Write a chat to disk."""
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(chat.id)
        path.write_text(
            json.dumps(chat.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    def all(self) -> List[Chat]:
        """Return all chats."""
        return self.chats

    def add(self, chat: Chat) -> None:
        """Add a chat and persist it."""
        self.chats.append(chat)
        self.save(chat)

    def remove(self, chat: Chat) -> None:
        """Remove a chat from memory and delete its JSON file."""
        if chat in self.chats:
            self.chats.remove(chat)
        path = self._path_for(chat.id)
        if path.is_file():
            path.unlink()

    def get(self, chat_id: str) -> Optional[Chat]:
        """Return the chat with the given id, or None."""
        for chat in self.chats:
            if chat.id == chat_id:
                return chat
        return None

    def is_empty(self) -> bool:
        """Return True if there are no chats."""
        return not self.chats
