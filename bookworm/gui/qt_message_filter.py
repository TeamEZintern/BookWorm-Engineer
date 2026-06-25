"""Route known-benign Qt warnings to a log file instead of stderr."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import qInstallMessageHandler

# Qt warnings treated as benign: hidden from stderr but appended for debugging.
_BENIGN_QT_MESSAGES = (
    "QWidget::mapFrom(): parent must be in parent hierarchy",
)

_BENIGN_LOG_NAME = "qt-benign.log"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEBUG_DIR = _REPO_ROOT / "debug"

_QtMessageHandler = Callable[..., None]
_previous_handler: Optional[_QtMessageHandler] = None
_benign_log_path: Optional[Path] = None


def benign_qt_log_path() -> Path:
    """Return the path used for known-benign Qt message logging."""
    return _DEBUG_DIR / _BENIGN_LOG_NAME


def _default_qt_message_handler(msg_type, _context, message: str) -> None:
    del msg_type
    sys.stderr.write(f"{message}\n")


def _format_context(context) -> str:
    if context is None:
        return ""
    parts = []
    if getattr(context, "file", None):
        parts.append(f"{context.file}:{context.line}")
    if getattr(context, "function", None):
        parts.append(context.function)
    return f" [{', '.join(parts)}]" if parts else ""


def _append_benign_qt_log(msg_type, context, message: str) -> None:
    if _benign_log_path is None:
        return
    log_path = _benign_log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    level = getattr(msg_type, "name", str(msg_type))
    line = f"{timestamp} [{level}] {message}{_format_context(context)}\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _filtered_qt_message_handler(msg_type, context, message: str) -> None:
    if any(snippet in message for snippet in _BENIGN_QT_MESSAGES):
        _append_benign_qt_log(msg_type, context, message)
        return
    handler = _previous_handler or _default_qt_message_handler
    handler(msg_type, context, message)


def install_gui_qt_message_filter() -> None:
    """Hide known-benign Qt warnings from stderr; append them to ``debug/qt-benign.log``."""
    global _previous_handler, _benign_log_path
    _benign_log_path = benign_qt_log_path()
    _previous_handler = qInstallMessageHandler(_filtered_qt_message_handler)
