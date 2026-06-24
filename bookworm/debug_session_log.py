"""Append-only NDJSON debug logging for the active debug session."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

_LOG_PATH = Path(__file__).resolve().parents[1] / "debug-54682e.log"
_SESSION_ID = "54682e"


def debug_log(
    location: str,
    message: str,
    data: Optional[dict[str, Any]] = None,
    *,
    hypothesis_id: Optional[str] = None,
    run_id: str = "pre-fix",
) -> None:
    # #region agent log
    entry = {
        "sessionId": _SESSION_ID,
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data or {},
        "hypothesisId": hypothesis_id,
        "runId": run_id,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    # #endregion
