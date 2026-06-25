from __future__ import annotations

import enum
from pathlib import Path
from typing import Callable


class CommandResult(enum.Enum):
    NOT_A_COMMAND = 0
    HANDLED = 1
    EXIT = 2


VALID_MODES = {"plan", "build", "research"}


def _cmd_init(working_dir: Path, output: Callable[[str], None]) -> CommandResult:
    sources_dir = working_dir / ".bookworm" / "sources"
    index_dir = working_dir/".bookworm"/"index"
    sources_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    output("Initialized .bookworm directory in the project root.")
    return CommandResult.HANDLED


def _cmd_exit(output: Callable[[str], None]) -> CommandResult:
    output("Exiting BookWorm Engineer. Goodbye!")
    return CommandResult.EXIT


def _cmd_help(output: Callable[[str], None]) -> CommandResult:
    output(
        "Commands:\n"
        "  /init                         — create .bookworm directory in the project\n"
        "  /mode <plan|build|research>   — change the agent's behavior mode\n"
        "  /exit, /quit                  — leave BookWorm Engineer\n"
        "  /help                         — show this message\n"
        "\n"
        "Special commands must start with '/' and cannot include extra text after "
        "their expected arguments."
    )
    return CommandResult.HANDLED


def _cmd_mode_switch(
    new_mode: str,
    set_mode: Callable[[str], None],
    output: Callable[[str], None],
) -> CommandResult:
    if new_mode in VALID_MODES:
        set_mode(new_mode)
        output(f"Switched to {new_mode.capitalize()} mode.")
    else:
        output(f"Unknown mode '{new_mode}'. Available: {', '.join(sorted(VALID_MODES))}.")
    return CommandResult.HANDLED


def handle_command(
    text: str,
    working_dir: Path,
    set_mode: Callable[[str], None],
    output: Callable[[str], None] = print,
) -> CommandResult:
    stripped = text.strip()
    if not stripped.startswith("/"):
        return CommandResult.NOT_A_COMMAND

    parts = stripped[1:].split()
    if not parts:
        return CommandResult.NOT_A_COMMAND

    command = parts[0].lower()
    args = parts[1:]

    if command == "init":
        if args:
            output("Usage: /init")
            return CommandResult.HANDLED
        return _cmd_init(working_dir, output)

    if command in {"exit", "quit"}:
        if args:
            output(f"Usage: /{command}")
            return CommandResult.HANDLED
        return _cmd_exit(output)

    if command == "mode":
        if len(args) != 1:
            output("Usage: /mode <plan|build|research>")
            return CommandResult.HANDLED
        return _cmd_mode_switch(args[0].lower(), set_mode, output)

    if command == "help":
        if args:
            output("Usage: /help")
            return CommandResult.HANDLED
        return _cmd_help(output)

    output(f"Unknown command '/{command}'. Type /help for available commands.")
    return CommandResult.HANDLED
