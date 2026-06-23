"""
Thread Store

Loads and saves conversation threads as JSON files under ``.bookworm/threads/``.
Each thread is stored as ``<thread_id>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .thread import Thread


class ThreadStore:
    """In-memory thread list backed by JSON files on disk."""

    def __init__(self, threads_dir: Path, threads: Optional[List[Thread]] = None):
        self.threads_dir = threads_dir
        self.threads: List[Thread] = threads or []

    def _path_for(self, thread_id: str) -> Path:
        return self.threads_dir / f"{thread_id}.json"

    def load(self) -> List[Thread]:
        """Load all threads from ``.bookworm/threads/``."""
        self.threads_dir.mkdir(parents=True, exist_ok=True)
        loaded: List[Thread] = []

        for path in sorted(self.threads_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                loaded.append(Thread.from_dict(data))
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                continue

        self.threads = loaded
        return self.threads

    def save(self, thread: Thread) -> None:
        """Write a thread to disk."""
        self.threads_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(thread.id)
        path.write_text(
            json.dumps(thread.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    def all(self) -> List[Thread]:
        """Return all threads."""
        return self.threads

    def add(self, thread: Thread) -> None:
        """Add a thread and persist it."""
        self.threads.append(thread)
        self.save(thread)

    def remove(self, thread: Thread) -> None:
        """Remove a thread from memory and delete its JSON file."""
        if thread in self.threads:
            self.threads.remove(thread)
        path = self._path_for(thread.id)
        if path.is_file():
            path.unlink()

    def get(self, thread_id: str) -> Optional[Thread]:
        """Return the thread with the given id, or None."""
        for thread in self.threads:
            if thread.id == thread_id:
                return thread
        return None

    def is_empty(self) -> bool:
        """Return True if there are no threads."""
        return not self.threads
