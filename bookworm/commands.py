from __future__ import annotations

import enum
from pathlib import Path
from typing import Callable


class CommandResult(enum.Enum):
    NOT_A_COMMAND = 0
    HANDLED = 1
    EXIT = 2


VALID_MODES = {"plan", "build", "research"}


def _cmd_init(working_dir: Path) -> CommandResult:
    sources_dir = working_dir / ".bookworm" / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    print("Initialized .bookworm directory in the project root.\n")
    return CommandResult.HANDLED


def _cmd_exit() -> CommandResult:
    print("Exiting BookWorm Engineer. Goodbye!")
    return CommandResult.EXIT


def _cmd_help() -> CommandResult:
    print(
        "Commands:\n"
        "  init                                — create .bookworm directory in the project\n"
        "  mode switch <plan|build|research>  — change the agent's mode\n"
        "  exit / quit                         — leave BookWorm Engineer\n"
        "  help                                — show this message\n"
    )
    return CommandResult.HANDLED


def _cmd_mode_switch(text: str, set_mode: Callable[[str], None]) -> CommandResult:
    new_mode = text[12:].strip().lower()
    if new_mode in VALID_MODES:
        set_mode(new_mode)
        print(f"Switched to {new_mode.capitalize()} mode.\n")
    else:
        print(f"Unknown mode '{new_mode}'. Available: {', '.join(sorted(VALID_MODES))}\n")
    return CommandResult.HANDLED


def handle_command(
    text: str,
    working_dir: Path,
    set_mode: Callable[[str], None],
) -> CommandResult:
    lowered = text.lower()

    if lowered in {"init"}:
        return _cmd_init(working_dir)

    if lowered in {"exit", "quit"}:
        return _cmd_exit()

    if lowered.startswith("mode switch "):
        return _cmd_mode_switch(text, set_mode)

    if lowered == "help":
        return _cmd_help()

    return CommandResult.NOT_A_COMMAND
