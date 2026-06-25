"""Event callbacks for observable agent turns."""

from dataclasses import dataclass
from typing import Any, Callable, Optional


class TurnCancelledError(Exception):
    """Raised when an in-flight turn is stopped by the user."""


@dataclass
class TurnEventHandler:
    """Optional callbacks emitted while an agent turn runs."""

    on_text_delta: Optional[Callable[[str], None]] = None
    on_tool_call_started: Optional[Callable[[str, str, str], None]] = None
    on_tool_result: Optional[Callable[[str, str], None]] = None
    on_reasoning_delta: Optional[Callable[[str], None]] = None
    on_turn_complete: Optional[Callable[[str, list[dict[str, Any]]], None]] = None
    on_error: Optional[Callable[[str], None]] = None
