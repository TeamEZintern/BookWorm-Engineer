import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str 
    ok: bool
    log: str
    files: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    skipped: bool = False

@dataclass
class ValidationResult:
    ok: bool
    log: str
    checks: list[CheckResult] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "failed_files": self.failed_files,
            "checks": [asdict(check) for check in self.checks],
            "log": self.log
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
# ---------- Command helpers ------------------------------------

def _run(command: list[str], cwd: Path, timeout: int = 200) -> tuple[bool, str, str, str]:
    """
    Run a command a return: 
        command_ok, combined_log, stdout, stderr
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        joined = " ".join(command)
        log = f"$ {joined}\nTimed out after {timeout}s.\n{exc}"
        return False, log, "", str(exc)
    except Exception as exc: 
        joined = " ".join(command)
        log = f"$ {joined}\nFailed to run command: {exc}"
        return False, log, "", str(exc)
    
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    output = stdout + stderr
    joined = " ".join(command)
    log = f"$ {joined}\n{output.strip() or '(no output)'}"
    
    return result.returncode == 0, log, stdout, stderr

def _normalise_file(path: str | Path) -> str:
    return str(path).replace("\\", "/")

def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))

def _python_files(output_dir: Path, include_tests: bool = True) -> list[Path]:
    files: list[Path] = []

    for path in output_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        
        if not include_tests and _is_test_file(path.relative_to(output_dir)):
            continue

        files.append(path)

    return sorted(files)

def _is_test_file(path: Path) -> bool:
    parts = {_normalise_file(part) for part in path.parts}
    return(
        "tests" in parts
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
    )

def _has_pytest_tests(output_dir: Path) -> bool:
    for path in output_dir.rglob("test_*.py"):
        if path.is_file():
            return True
        
    for path in output_dir.rglob("*_test.py"):
        if path.is_file():
            return True
        
    return False

#----------- File extraction helpers ----------------------------

def _extract_compile_files(output: str, output_dir: Path) -> list[str]:
    """
    compileall output commonly contains lines like:
        ***Error compiling './main.pt'...
        File "./models/foo.py", line 3
    """
    files: list[str] = []

    patterns = [
        r"Error compiling ['\"](?P<file>.+?\.py)['\"]",
        r'File "?(?P<file>[^"\n]+?\.py)"?, line \d+',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern,output):
            raw_file = match.group("file")
            files.append(_make_relative_file(raw_file, output_dir))

    return _dedupe(files)

def _extract_pytest_files(output: str, output_dir: Path) -> list[str]:
    files: list[str] = []

    patterns = [
        r"(?P<file>(?:tests/)?[^:\s]+\.py):\d+",
        r"ERROR collecting (?P<file>[^:\n]+\.py)",
        r"FAILED (?P<file>[^:\s]+\.py)::",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, output.replace("\\","/")):
            files.append(_make_relative_file(match.group("file"),output_dir))

    return _dedupe(files)

def _make_relative_file(raw_file: str, output_dir: Path) -> str:
    raw = raw_file.strip().strip("'\"").replace("\\","/")

    if raw.startswith("./"):
        raw = raw[2:]

    path = Path(raw)

    if path.is_absolute():
        try: 
            return _normalise_file(path.relative_to(output_dir))
        except ValueError:
            return _normalise_file(path.name)
        
    return _normalise_file(raw)

def _ruff_json_to_files_and_diagnositcs(
        stdout: str,
        stderr: str,
        output_dir: Path,
) -> tuple[list[str], list[str]]:
    """
    Parse `ruff check . --output-format=json`.

    Ruff JSON is usually a list of objects:
        {
            "filename": "...",
            "code": "F401",
            "message": "...",
            "location": {"row": 1, "column": 1}
        }
    """
    raw = stdout.strip() or stderr.strip()

    if not raw: 
        return [], []
    
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return [], [raw]
    
    if not isinstance(parsed, list):
        return [], [raw]
    
    files: list[str] = []
    diagnostics: list[str] = []

    for item in parsed:
        if not isinstance(item, dict):
            continue

        filename = item.get("filename")
        if not filename:
            continue

        relative_file = _make_relative_file(str(filename), output_dir)
        files.append(relative_file)

        code = item.get("code") or "RUFF"
        message = item.get("message") or "Ruff diagnostic"

        location = item.get("location") or {}
        row = location.get("row", "?")
        column = location.get("column", "?")

        diagnostics.append(f"{relative_file}:{row}:{column}: {code} {message}")

    return _dedupe(files), diagnostics

#----------- Individual validation phases -----------------------

def _run_compile_check(output_dir: Path) -> CheckResult:
    command = [sys.executable, "-m", "compileall", "-q", "."]
    ok, log, stdout, stderr = _run(command, output_dir)

    output = stdout + stderr
    files = [] if ok else _extract_compile_files(output, output_dir)

    diagnostics = []
    if not ok:
        diagnostics.append(output.strip() or "compileall failed")

    return CheckResult(
        name="compileall",
        ok=ok,
        log=log,
        files=files,
        diagnostics=diagnostics,
    )

def _run_import_smoke_tests(output_dir: Path) -> CheckResult:
    python_files = _python_files(output_dir, include_tests=False)

    logs: list[str] = []
    files: list[str] = []
    diagnostics: list[str] = []
    ok = True

    if not python_files:
        return CheckResult(
            name = "import_smoke",
            ok=ok,
            log="No implementation Python files found for import smoke tests.",
            files=[],
            diagnostics=[],
            skipped=True,
        )
    
    for path in python_files:
        relative_path = path.relative_to(output_dir)
        module_path = relative_path.with_suffix("")
        module_name = ".".join(module_path.parts)

        command = [
            sys.executable,
            "-c",
            f"import {module_name}",
        ]

        command_ok, log, stdout, stderr = _run(command, output_dir)
        logs.append(log)

        if not command_ok:
            ok = False
            relative_path = _normalise_file(relative_path)
            files.append(relative_path)
            diagnostics.append(
                f"{relative_path}: import failed for module `{module_name}`\n"
                f"{(stdout + stderr).strip()}"
            )
        
    return CheckResult(
        name="import_smoke",
        ok=ok,
        log="\n\n".join(logs),
        files=_dedupe(files),
        diagnostics=diagnostics,
    )

def _run_ruff_autofix(output_dir: Path) -> CheckResult:
    """
    Run deterministic ruff fixes first.

    --exit-zero is intentional because this pahse is not the final lint gate
    Remaining issues are checked by _run_ruff_check_json().
    """
    command = [sys.executable, "-m", "ruff", "check", ".", "--fix", "--unsafe-fixes", "--exit-zero"]
    ok, log, _stdout, _stderr = _run(command, output_dir)

    return CheckResult(
        name="ruff_autofix",
        ok=ok,
        log=log,
        files=[],
        diagnostics=[] if ok else ["ruff autofix command failed to run"],
    )

def _run_ruff_check_json(output_dir: Path) -> CheckResult:
    command = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        ".",
        "--output-format=json",
    ]

    ok, log, stdout, stderr = _run(command, output_dir)
    files, diagnostics = _ruff_json_to_files_and_diagnositcs(stdout, stderr, output_dir)

    if not ok and not diagnostics:
        diagnostics = [(stdout + stderr).strip() or "ruff check failed"]

    return CheckResult(
        name="ruff",
        ok=ok,
        log=log,
        files=files,
        diagnostics=diagnostics,
    )

def _run_pytest_check(output_dir: Path) -> CheckResult:
    if not _has_pytest_tests(output_dir):
        return CheckResult(
            name="pytest",
            ok=True,
            log="No pytest found; skipped pytest.",
            files=[],
            diagnostics=[],
            skipped=True,
        )
    """
    --continue-on-collection-errors: 
        if pytest fails to import/collect some test files, keep going and run the ones it could collect instead of aborting
    --tb=short: 
        on failures, show a shortened traceback (just the relevant lines) rather than the full one
    -ra: 
        after the run, print a summary of all non-passing tests (failed, errored, skipped, xfailed, etc.). The a means "all except passed"
    """
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--continue-on-collection-errors",
        "--tb=short",
        "-ra",
    ]

    ok, log, stdout, stderr = _run(command,output_dir)
    output = stdout + stderr
    
    files = [] if ok else _extract_pytest_files(output, output_dir)
    diagnostics = [] if ok else [output.strip() or "pytest failed"]

    return CheckResult(
        name="pytest",
        ok=ok,
        log=log,
        files=files,
        diagnostics=diagnostics,
    )

def _skipped_check(name: str, reason: str) -> CheckResult:
    return CheckResult(
        name=name,
        ok=True,
        log=reason,
        files=[],
        diagnostics=[],
        skipped=True,
    )

#----------- Public helpers used by pipeline.py --------------------

def _load_validated_or_initial_code(
    artifacts_dir: Path,
    task_list: list[str],
    initial_files: dict[str, str],
    artifacts,
) -> dict[str, str]:
    """
    Load the best available code for validation.

    Priority:
      1. candidate_code/<filename>.txt
      2. validated_code/<filename>.txt
      3. initial_files[filename]
    """
    files: dict[str, str] = {}

    for filename in task_list:
        candidate = artifacts.load(artifacts_dir, f"candidate_code/{filename}.txt")
        validated = artifacts.load(artifacts_dir, f"validated_code/{filename}.txt")

        if candidate is not None:
            files[filename] = candidate
        elif validated is not None:
            files[filename] = validated
        else:
            files[filename] = initial_files[filename]

    return files

def _run_validation(output_dir: Path) -> ValidationResult:
    """
    Run validation in gated order: 

        1. compileall
        2. import smoke tests
        3. ruff autofix
        4. ruff JSON lint
        5. pytest

    Pytest is skipped if syntax/import/lint gates fail. This prevents a misleading 
    "pytest passed" result from higing a broken repository
    """

    checks: list[CheckResult] = []

    compile_result = _run_compile_check(output_dir)
    checks.append(compile_result)

    if not compile_result.ok:
        checks.append(_skipped_check("import_smoke", "Skipped because compileall failed."))
        checks.append(_skipped_check("ruff_autofix", "Skipped because compileall failed."))
        checks.append(_skipped_check("ruff", "Skipped because compileall failed."))
        checks.append(_skipped_check("pytest", "Skipped because compileall failed."))
        return _build_validation_result(checks)
    
    import_result = _run_import_smoke_tests(output_dir)
    checks.append(import_result)

    if not import_result.ok:
        checks.append(_skipped_check("ruff_autofix", "Skipped because import smoke tests failed."))
        checks.append(_skipped_check("ruff", "Skipped because import smoke tests failed."))
        checks.append(_skipped_check("pytest", "Skipped because import smoke tests failed."))
        return _build_validation_result(checks)
    
    ruff_fix_result = _run_ruff_autofix(output_dir)
    checks.append(ruff_fix_result)

    if not ruff_fix_result.ok:
        checks.append(_skipped_check("ruff", "Skipped because ruff autofix failed to run."))
        checks.append(_skipped_check("pytest", "Skipped because ruff autofix failed to run."))
        return _build_validation_result(checks)
    
    ruff_result = _run_ruff_check_json(output_dir)
    checks.append(ruff_result)

    pytest_result = _run_pytest_check(output_dir)
    checks.append(pytest_result)

    return _build_validation_result(checks)
    
def _build_validation_result(checks: list[CheckResult]) -> ValidationResult:
    failed_files: list[str] = []
    logs: list[str] = []

    for check in checks:
        logs.append(f"## {check.name}\n{check.log}")

        if not check.ok:
            failed_files.extend(check.files)

    failed_files = _dedupe(failed_files)
    ok = all(check.ok for check in checks)

    return ValidationResult(
        ok=ok,
        log="\n\n".join(logs),
        checks=checks,
        failed_files=failed_files,
    )