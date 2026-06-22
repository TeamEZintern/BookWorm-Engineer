"""
UI Build Script

Walks the ``views/`` directory tree, finds every Qt Designer ``.ui`` file, and
runs ``pyside6-uic`` to regenerate the matching ``ui_<name>.py`` in the same
folder.

Usage:

    python -m bookworm.gui.build_ui

Notes:
- Generated ``ui_*.py`` files must NOT be hand-edited; changes are lost on
  regeneration.
- ``pyside6-uic`` is invoked via ``python -m PySide6.scripts.pyside_tool uic``
  so it always resolves against the interpreter running this script (e.g. the
  project's conda environment), avoiding version mismatches.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

VIEWS_DIR = Path(__file__).resolve().parent / "views"


def find_ui_files(views_dir: Path = VIEWS_DIR) -> List[Path]:
    """Return all ``.ui`` files under ``views_dir``."""
    return sorted(views_dir.rglob("*.ui"))


def output_path(ui_file: Path) -> Path:
    """Return the ``ui_<name>.py`` path for a given ``.ui`` file."""
    return ui_file.with_name(f"ui_{ui_file.stem}.py")


def convert(ui_file: Path) -> Path:
    """Run ``pyside6-uic`` on a single ``.ui`` file. Returns the output path."""
    out_file = output_path(ui_file)
    cmd = [
        sys.executable,
        "-m",
        "PySide6.scripts.pyside_tool",
        "uic",
        str(ui_file),
        "-o",
        str(out_file),
    ]
    subprocess.run(cmd, check=True)
    return out_file


def build_all(views_dir: Path = VIEWS_DIR) -> List[Path]:
    """Convert every ``.ui`` file under ``views_dir``. Returns output paths."""
    outputs: List[Path] = []
    for ui_file in find_ui_files(views_dir):
        out_file = convert(ui_file)
        print(f"{ui_file.relative_to(views_dir.parent)} -> {out_file.name}")
        outputs.append(out_file)
    return outputs


def main() -> int:
    ui_files = find_ui_files()
    if not ui_files:
        print(f"No .ui files found under {VIEWS_DIR}", file=sys.stderr)
        return 1
    build_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
