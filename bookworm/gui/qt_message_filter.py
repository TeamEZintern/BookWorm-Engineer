"""Filter noisy Qt warnings that do not affect GUI behaviour."""

from __future__ import annotations

import sys
from typing import Callable, Optional

from PySide6.QtCore import qInstallMessageHandler

# Harmless Qt warning when coordinate mapping runs during widget teardown.
_SUPPRESSED_MESSAGES = (
    "QWidget::mapFrom(): parent must be in parent hierarchy",
)

_QtMessageHandler = Callable[..., None]
_previous_handler: Optional[_QtMessageHandler] = None


def _default_qt_message_handler(msg_type, _context, message: str) -> None:
    del msg_type
    sys.stderr.write(f"{message}\n")


def _filtered_qt_message_handler(msg_type, context, message: str) -> None:
    if any(snippet in message for snippet in _SUPPRESSED_MESSAGES):
        return
    handler = _previous_handler or _default_qt_message_handler
    handler(msg_type, context, message)


def install_gui_qt_message_filter() -> None:
    """Suppress known-benign Qt warnings on stderr."""
    global _previous_handler
    _previous_handler = qInstallMessageHandler(_filtered_qt_message_handler)
