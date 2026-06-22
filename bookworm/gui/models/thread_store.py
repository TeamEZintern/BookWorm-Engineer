"""
Thread Store

In-memory store for conversation threads. Provides a single place to hold and
mutate the thread list. Disk persistence under ``.bookworm/threads/`` is not yet
implemented (see design.md) and ``load()`` currently returns an empty list,
preserving the previous start-empty behaviour.
"""

from typing import List, Optional

from .thread import Thread


class ThreadStore:
    """Holds the in-memory list of threads."""

    def __init__(self, threads: Optional[List[Thread]] = None):
        self.threads: List[Thread] = threads or []

    def load(self) -> List[Thread]:
        """Load threads from storage.

        Persistence is not yet implemented, so this starts with an empty list.
        """
        # TODO: Implement thread loading from .bookworm/threads/
        self.threads = []
        return self.threads

    def all(self) -> List[Thread]:
        """Return all threads."""
        return self.threads

    def add(self, thread: Thread) -> None:
        """Add a thread to the store."""
        self.threads.append(thread)

    def remove(self, thread: Thread) -> None:
        """Remove a thread from the store."""
        if thread in self.threads:
            self.threads.remove(thread)

    def get(self, thread_id: str) -> Optional[Thread]:
        """Return the thread with the given id, or None."""
        for thread in self.threads:
            if thread.id == thread_id:
                return thread
        return None

    def is_empty(self) -> bool:
        """Return True if there are no threads."""
        return not self.threads
