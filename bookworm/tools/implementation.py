import os
import shlex
import subprocess
from pathlib import Path
from typing import Callable

from ..config import Config
from ..rag.retriever import retrieve_context
from .schema import ALLOWED_COMMAND_PREFIXES, SHELL_TIMEOUT

def _resolve_inside_working_dir(working_dir: Path, file_path: str) -> Path:
    root = working_dir.resolve()
    path = (root / file_path).resolve()

    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes working directory: {file_path}")

    return path


def create_implementations(config: Config) -> dict[str, Callable[..., str]]:
    working_dir = config.working_dir

    def read_file(file_path: str) -> str:
        print(f"  → read_file: {file_path}")
        path = _resolve_inside_working_dir(working_dir, file_path)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"Error: {file_path} not found."
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    def write_file(file_path: str, content: str) -> str:
        print(f"  → write_file: {file_path}")
        abs_file_path = _resolve_inside_working_dir(working_dir, file_path)
        try:
            abs_file_path.parent.mkdir(parents=True, exist_ok=True)
            abs_file_path.write_text(content, encoding="utf-8")
            return f"Written to {file_path}"
        except Exception as e:
            return f"Error writing {file_path}: {e}"

    def bash(command: str) -> str:
        print(f"  → bash: {command}")
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            return f"Error parsing command: {e}"

        if not tokens:
            return "Error: empty command."

        cmd_name = os.path.basename(tokens[0]).lower().removesuffix(".exe")

        if not any(cmd_name == prefix or cmd_name.startswith(prefix) for prefix in ALLOWED_COMMAND_PREFIXES):
            return (
                f"Error: '{tokens[0]}' is not permitted. "
                f"Allowed commands: {', '.join(ALLOWED_COMMAND_PREFIXES)}"
            )

        # Build a minimal environment — enough for Python/pip to run, nothing extra.
        # Inheriting the full host env risks leaking credentials or PATH manipulation.
        # See: https://securecodingpractices.com/prevent-command-injection-python-subprocess/
        safe_env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if k in os.environ}
        # Pass through conda and Python env vars so the correct interpreter is used.
        for k, v in os.environ.items():
            if k.startswith(("CONDA_", "PYTHON", "VIRTUAL_ENV")):
                safe_env[k] = v

        try:
            result = subprocess.run(
                command,
                shell=True,           # needed for compound commands and pipes
                cwd=working_dir,              # locked to project root by caller
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=SHELL_TIMEOUT
            )
            output = result.stdout + result.stderr
            return output.strip() if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {SHELL_TIMEOUT}s."
        except Exception as e:
            return f"Error running command: {e}"
        
    def ask_user(question: str) -> str:
        print(f"  → ask_user: {question}")
        user_response = input("  > ").strip()
        print()
        return user_response
    
    def search_sources(query: str) -> str:
        query_preview = query[:80] + "…" if len(query) > 80 else query
        print(f"  → search_sources: {query_preview}")
        result = retrieve_context(config, query)
        return result if result else "(no matching sources found in the RAG index)"
    return {
        "read_file": read_file,
        "write_file": write_file,
        "bash": bash,
        "ask_user": ask_user,
        "search_sources": search_sources,
    }