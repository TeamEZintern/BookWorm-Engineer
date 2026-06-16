import py_compile
import subprocess
import sys
from pathlib import Path


def check_syntax(file_path: Path) -> str | None:
    try:
        py_compile.compile(str(file_path), doraise=True)
        return None
    except py_compile.PyCompileError as exc:
        return str(exc)


def install_packages(packages: list[str], cwd: Path) -> str:
    if not packages:
        return "No packages listed."

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", *packages],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return "pip install timed out after 600s."

    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return f"pip install failed:\n{output}"
    return "Packages installed successfully."


def smoke_test(entry_point: Path, cwd: Path, timeout: int = 30) -> str | None:
    try:
        result = subprocess.run(
            [sys.executable, str(entry_point)],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None

    if result.returncode == 0:
        return None

    return (result.stdout + result.stderr).strip()