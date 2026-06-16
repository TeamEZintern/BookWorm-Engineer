from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from . import artifacts, prompts

#--------------- Helper functions for validation-------------------------------
@dataclass
class ValidationResult:
    ok: bool
    log: str

def _run(command: list[str], cwd: Path, timeout: int = 200) -> tuple[bool,str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"${' '.join(command)}\nTimed out after {timeout}s.\n{exc}"
    except Exception as exc:
        return False, f"${' '.join(command)}\nFailed to run command: {exc}"
    
    output = result.stdout + result.stderr
    log = f"$ {' '.join(command)}\n{output.strip() or '(no output)'}"
    return result.returncode == 0, log

def _has_pytest_tests(output_dir: Path) -> bool:
    test_roots = [output_dir / "tests", output_dir]
    for root in test_roots: 
        if not root.exists():
            continue
        for path in root.rglob("test_*.py"):
            if path.is_file():
                return True
        for path in root.rglob("*_test.py"):
            if path.is_file():
                return True
    return False

def _is_test_file(path: Path) -> bool:
    return (
        "tests" in path.parts
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
    )

def _run_import_smoke_tests(output_dir: Path) -> ValidationResult:
    python_files = [
        path for path in output_dir.rglob("*.py")
        if "__pycache__" not in path.parts and not path.name.startswith("test_")
    ]

    logs = []
    ok = True

    for path in python_files:
        module_path = path.relative_to(output_dir).with_suffix("")
        module_name = ".".join(module_path.parts)

        command = [
            sys.executable,
            "-c",
            f"import {module_name}",
        ]

        command_ok, log = _run(command, output_dir)
        logs.append(log)

        if not command_ok:
            ok = False
    
    if not logs: 
        logs.append("No implementation Python files found for import smoke tests")

    return ValidationResult(ok=ok, log="\n\n".join(logs))

def _load_validated_or_initial_code(
    artifacts_dir: Path,
    task_list: list[str],
    initial_files: dict[str, str],
    artifacts: artifacts
) -> dict[str, str]:
    files: dict[str, str] = {}

    for filename in task_list:
        validated = artifacts.load(artifacts_dir, f"validated_code/{filename}.txt")
        files[filename] = validated if validated is not None else initial_files[filename]

    return files

def _run_validation(output_dir: Path) -> ValidationResult:
    checks: list[tuple[str,list[str]]] = [
        ("compileall",[sys.executable, "-m", "compileall", "-q", "."]),
        ("ruff",[sys.executable, "-m", "ruff", "check", "."]),
    ]

    logs: list[str] = []
    ok = True

    for name, command in checks:
        command_ok, log = _run(command, output_dir)
        logs.append(f"## {name}\n{log}")
        if not command_ok:
            ok = False

    import_result = _run_import_smoke_tests(output_dir)
    logs.append(f"## import smoke tests\n{import_result.log}")
    if not import_result.ok:
        ok = False

    if _has_pytest_tests(output_dir):
        command = [sys.executable, "-m", "pytest", "--continue-on-collection-errors", "--tb=short", "-ra"]
        command_ok, log = _run(command, output_dir)
        logs.append(f"## pytest\n{log}")

        if not command_ok:
            ok = False
    else:
        logs.append("## pytest\nNo pytests found; skipped pytest.")

    return ValidationResult(ok=ok, log="\n\n".join(logs))