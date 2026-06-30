import json
import re
from pathlib import Path

from openai import OpenAI
import os

from ..config import Config
from . import artifacts, prompts
from .pdf import extract_text
from .validation import _load_validated_or_initial_code,_run_validation,ValidationResult
from ..llm import complete_with_retry

MAX_VALIDATION_ATTEMPTS = 6
JSON_MAX_ATTEMPTS = 3

def _llm(client: OpenAI, config: Config, system: str, user: str) -> str:
    response = complete_with_retry(
        client=client,
        model=config.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""

def _llm_json(client: OpenAI, config: Config, system: str, user: str, *,stage_name:str, max_attempts: int = JSON_MAX_ATTEMPTS) -> tuple[dict, str]:
    """
    Call the LLM expecting a JSON object. On a parse failure, feed the bad output back with a corrective message
    and re-roll(content-level retry).
    This is separate from complete_with_retry (transport-level retry): 
        each attempt here still goes through complete_with_retry, so transient HTTP failures are handled underneath.
    Returns (parsed dict, raw_text_that_parsed).
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_error = ""

    for attempt in range(1, max_attempts + 1): 
        response = complete_with_retry(
            client=client, 
            model=config.llm_model,
            messages=messages
        )
        raw = response.choices[0].message.content or ""

        try: 
            return _extract_json(raw), raw
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = str(exc)
            print(f" {stage_name}: invalid JSON (attempt {attempt}/{max_attempts} - re-rolling...)")
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous response could not be parsed as JSON ({last_error})"
                    f"Reply with ONLY one valid JSON object - no prose, no markdown fences, and no array(`[...]`) at the top level"
                )
            })
    
    raise ValueError(
        f"{stage_name}: model did not return valid JSON after {max_attempts} attempts"
        f"(last error: {last_error})"
    )

def _fix_escapes(text: str) -> str:
    # Replace backslashes not part of a valid JSON escape with a literal \\
    # Valid JSON escapes after \: " \ / b f n r t u
    return re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", text)


def _extract_json(text: str) -> dict:
    # Try every fenced code block and return the first that parses as a dict.
    for match in re.finditer(r"```(?:json)?\s*([\s\S]+?)\s*```", text):
        for candidate in (match.group(1), _fix_escapes(match.group(1))):
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                continue

    # Fallback: find the outermost {...} span in the raw text.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = text[start : end + 1]
        for candidate in (raw, _fix_escapes(raw)):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError("No valid JSON object found in LLM response")

def _resolve_generated_path(root: Path, filename: str) -> Path:
      """Resolve an LLM-generated filename while keeping it inside root."""
      if not filename or not filename.strip():
          raise ValueError("Generated filename cannot be empty.")

      relative_path = Path(filename)

      if relative_path.is_absolute():
          raise ValueError(f"Generated path must be relative: {filename}")

      resolved_root = root.resolve()
      resolved_path = (resolved_root / relative_path).resolve()

      if not resolved_path.is_relative_to(resolved_root):
          raise ValueError(f"Generated path escapes output directory: {filename}")

      return resolved_path


def _extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text

def _write_files(output_dir: Path, files: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, code in files.items():
        output_path = _resolve_generated_path(output_dir, filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")

def _read_task_files(output_dir: Path, task_list: list[str]) -> dict[str, str]:
    """
    Read the current files from output_dir.

    This is important because validation may run determininstic tools like:
        Ruff check . --fix
    
    That means the files on disk may become newer than current_files in memory.
    """
    files: dict[str, str] = {}

    for filename in task_list:
        path = _resolve_generated_path(output_dir, filename)
        if path.exists():
            files[filename] = path.read_text(encoding="utf-8")
    
    return files

def _save_files_artifact(artifacts_dir: Path, prefix: str,files: dict[str,str]) -> None:
    """
    Save a dictionary of filename -> content into the artifact directory.

    Example:
        _save_files_artifact(
            artifacts_dir,
            "validation/attempt_1/files",
            current_files,
        )

    Produces:
        validation/attempt_1/files/main.py.txt
        validation/attempt_1/files/models/model.py.txt
        validation/attempt_1/files/tests/test_model.py.txt
    """
    artifact_root = _resolve_generated_path(artifacts_dir, prefix)
    artifact_root.mkdir(parents=True, exist_ok=True)

    for filename, content in files.items():
        path = _resolve_generated_path(artifact_root, f"{filename}.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

def _extract_affected_files(log: str, task_list: list[str]) -> list[str]:
    affected: list[str] = []

    normalized_log = log.replace("\\", "/")

    for filename in task_list:
        normalized_filename = filename.replace("\\","/")
        basename = Path(filename).name

        if normalized_filename in normalized_log or basename in normalized_log:
            affected.append(filename)

    return affected or task_list

def _triage_failure(
    client: OpenAI,
    config: Config,
    validation_log: str,
    task_list: list[str],
    validation_report_json: str,
) -> dict:
    raw = _llm(
        client,
        config,
        prompts.TRIAGE_SYSTEM,
        prompts.triage_prompt(validation_log, task_list, validation_report_json)
    )
    return _extract_json(raw)

def _match_task_files(candidate_files: list[str], task_list: list[str]) -> list[str]:
    normalized_tasks = {
        filename.replace("\\", "/"): filename
        for filename in task_list
    }

    matched: list[str] = []

    for candidate in candidate_files:
        normalized = candidate.replace("\\","/")

        if normalized in normalized_tasks:
            matched.append(normalized_tasks[normalized])
            continue

        # Sometimes logs/LLM triage only return basename, e.g. "main.py".
        candidate_basename = Path(normalized).name
        for normalized_task, original_task in normalized_tasks.items():
            if Path(normalized_task).name == candidate_basename:
                matched.append(original_task)

    return list(dict.fromkeys(matched))

def _affected_files_from_triage(
        triage: dict,
        task_list: list[str],
        fallback_files: list[str],
) -> tuple[list[str], list[dict]]:
    repairable_failures: list[dict] = []
    dependency_issues: list[dict] =[]

    for failure in triage.get("failures", []):
        classification = failure.get("classification")
        if classification == "dependency_issue":
            dependency_issues.append(failure)
        else: 
            repairable_failures.append(failure)
    
    affected_files: list[str] = []

    for failure in repairable_failures:

        candidate_files = failure.get("affected_files", [])
        if isinstance(candidate_files, list):
            affected_files.extend(_match_task_files(candidate_files, task_list))

    affected_files = list(dict.fromkeys(affected_files))

    # Only fall back to filename-based repair when at least one
    # failure is actually repairable.
    if repairable_failures and not affected_files:
        affected_files = fallback_files

    return affected_files, dependency_issues

def _build_validation_log_with_report(result, triage_json: str) -> str:
    """
    Build a repair log that includes both:
      1. human-readable validation log
      2. structured validation JSON
      3. triage JSON
    """
    return (
        result.log
        + "\n\n"
        + "Structured validation report:\n"
        + "```json\n"
        + result.to_json()
        + "\n```\n\n"
        + "Triage report:\n"
        + "```json\n"
        + triage_json
        + "\n```"
    )

def _failure_signature(result: ValidationResult) -> frozenset[str]:
    """
    Stable identity of a failing run, for stagnation detection.
    Keyed on failed files + pytest node ids - NOT raw log text, which 
    carries volatile timing lines that change every run."""
    signature = set(result.failed_files)
    for line in result.log.splitlines():
        match = re.match(r"(FAILED|ERROR)\s+(\S+)", line.strip())
        if match:
            signature.add(f"{match.group(1)} {match.group(2)}")
    return frozenset(signature)

def _save_validation_attempt(artifacts_dir: Path, attempt: int, result: ValidationResult, files:dict[str, str]) -> None:
    """
    Save full validation artifacts for one attempt.

    This gives a clean per-attempt snapshot:

        validation/attempt_1/validation.log
        validation/attempt_1/validation_report.json
        validation/attempt_1/files/...
    """

    artifacts.save(artifacts_dir,f"validation/attempt_{attempt}/validation.log",result.log)
    artifacts.save(artifacts_dir,f"validation/attempt_{attempt}/validation_report.json", result.to_json())
    _save_files_artifact(artifacts_dir,f"validation/attempt_{attempt}/files", files)

def _promote_validated_code(artifacts_dir: Path, files: dict[str, str]) -> None:
    """
    Only call this after the full repo passes validation.

    This keeps validated_code honest:
        - candidate code = latest repaired attempt
        - validated_code = passed full validation
    """
    _save_files_artifact(
        artifacts_dir,
        "validated_code",
        files,
    )

#------------------- Pipline Flow------------------------------------------
def run_pipeline(
    client: OpenAI,
    config: Config,
    paper_path: Path,
    output_dir: Path,
) -> str:
    paper_name = paper_path.stem
    artifacts_dir = config.working_dir / ".bookworm" / "paper2code" / paper_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting text from {paper_path.name}...")
    paper_text = extract_text(paper_path)

    # Stage 1a: Overall plan
    overall_plan = artifacts.load(artifacts_dir, "overall_plan.txt")
    if overall_plan is None:
        print("Planning: overall plan...")
        overall_plan = _llm(
            client, config,
            prompts.PLANNING_SYSTEM,
            prompts.overall_plan_prompt(paper_text),
        )
        artifacts.save(artifacts_dir, "overall_plan.txt", overall_plan)

    # Stage 1b: Success Criteria
    success_criteria_raw = artifacts.load(artifacts_dir,"success_criteria.json")
    if success_criteria_raw is None:
        print("Planning: success criteria...")
        try:
            success_criteria, _ = _llm_json(
                client,
                config,
                prompts.SUCCESS_CRITERIA_SYSTEM,
                prompts.success_criteria_prompt(paper_text, overall_plan),
                stage_name="success criteria"
            )
        except ValueError as exc: 
            return f"PIPELINE FAILED: {exc}"
        success_criteria_raw = json.dumps(success_criteria, indent=2)
        artifacts.save(artifacts_dir, "success_criteria.json",success_criteria_raw)

    # Stage 1c: Architecture
    architecture_raw = artifacts.load(artifacts_dir, "architecture.txt")
    if architecture_raw is None:
        print("Planning: architecture...")
        try: 
            architecture, architecture_raw = _llm_json(
                client, 
                config,
                prompts.PLANNING_SYSTEM,
                prompts.architecture_prompt(paper_text, overall_plan,success_criteria_raw),
                stage_name="architecture",
            )
        except ValueError as exc:
            return f"PIPELINE FAILED: {exc}" 
        
        artifacts.save(artifacts_dir, "architecture.txt", architecture_raw)
    else:
        try:
            architecture = _extract_json(architecture_raw)
        except (json.JSONDecodeError, ValueError) as exc:
            return f"PIPELINE FAILED: cached architecture.txt is not valid JSON: {exc}"
    
    # Stage 1d: Logic design
    logic_raw = artifacts.load(artifacts_dir, "logic_design.txt")
    if logic_raw is None:
        print("Planning: logic design...")
        try: 
            logic, logic_raw = _llm_json(
                client, config,
                prompts.PLANNING_SYSTEM,
                prompts.logic_design_prompt(paper_text, overall_plan, architecture_raw, success_criteria_raw),
                stage_name="logic_design"
            )
        except ValueError as exc:
            return f"PIPELINE FAILED: {exc}"
        artifacts.save(artifacts_dir, "logic_design.txt", logic_raw)
    else:
        try:
            logic = _extract_json(logic_raw)
        except (json.JSONDecodeError, ValueError) as exc:
            return f"Failed to parse logic design JSON: {exc}\n\nRaw response:\n{logic_raw}"

    task_list: list[str] = logic.get("task_list", [])
    file_logic: dict[str, str] = logic.get("logic", {})
    file_descriptions: dict[str, str] = {
        f["name"]: f["description"] for f in architecture.get("files", [])
    }

    if not task_list:
        return "Pipeline error: logic design returned an empty task list."

    # Stage 2: Analysis (one per file)
    print(f"Analyzing {len(task_list)} files...")
    analyses: dict[str, str] = {}
    for filename in task_list:
        artifact_name = f"analysis/{filename}.txt"
        analysis = artifacts.load(artifacts_dir, artifact_name)
        if analysis is None:
            print(f"  Analyzing {filename}...")
            analysis = _llm(
                client, config,
                prompts.ANALYSIS_SYSTEM,
                prompts.analysis_prompt(
                    paper_text,
                    overall_plan,
                    architecture_raw,
                    logic_raw,
                    filename,
                    file_descriptions.get(filename, file_logic.get(filename, "")),
                    success_criteria_raw,
                ),
            )
            artifacts.save(artifacts_dir, artifact_name, analysis)
        analyses[filename] = analysis

    # Stage 3: Coding (one per file, in dependency order)
    print(f"Coding {len(task_list)} files...")
    prior_files: dict[str, str] = {}
    for filename in task_list:
        artifact_name = f"code/{filename}.txt"
        code = artifacts.load(artifacts_dir, artifact_name)
        if code is None:
            print(f"  Coding {filename}...")
            raw = _llm(
                client, config,
                prompts.CODING_SYSTEM,
                prompts.coding_prompt(
                    paper_text,
                    overall_plan,
                    success_criteria_raw,
                    logic_raw,
                    filename,
                    analyses[filename],
                    prior_files,
                ),
            )
            code = _extract_code(raw)
            artifacts.save(artifacts_dir, artifact_name, code)

        prior_files[filename] = code

    # Stage 4: Validation and repair
    print("Validating generated code...")
    current_files = _load_validated_or_initial_code(
        artifacts_dir=artifacts_dir,
        task_list=task_list,
        initial_files=prior_files,
        artifacts=artifacts,
    )

    validation_ok = False
    stalled = False
    best_files = current_files.copy()
    best_signature: frozenset[str] | None = None
    seen_signatures: set[frozenset[str]] = set()

    for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
        _write_files(output_dir, current_files)

        result = _run_validation(output_dir)

        #Ruff autofix may have changes files on disk.
        disk_files = _read_task_files(output_dir, task_list)
        if disk_files: 
            current_files.update(disk_files)

        _save_validation_attempt(artifacts_dir,attempt,result,current_files)

        if result.ok:
            validation_ok = True
            artifacts.save(artifacts_dir, "validation/result.txt", "passed")

            _promote_validated_code(artifacts_dir,current_files)
            best_files = current_files
            break

        signature = _failure_signature(result)

        # Guard 1  keep-best: adopt this state as the repair base if it did NOT regress vs the best failing state seen so far
        if best_signature is None or len(signature) < len(best_signature):
            best_files = current_files.copy()
            best_signature = signature
        
        # Guard 2 - revisit/stagnation: this exact failing set already appeared
        # so repair is cycling, not converging. Stop instead of burning attempts.
        if signature in seen_signatures:
            stalled = True
            artifacts.save(artifacts_dir, "validation/result.txt", "stalled")
            print(f"Validation stalled at attempt {attempt}: failing set repeated; stopping.")
            break

        seen_signatures.add(signature)

        if attempt == MAX_VALIDATION_ATTEMPTS:
            artifacts.save(artifacts_dir,"validation/result.txt","failed")
            break

        structured_failed_files = _match_task_files(result.failed_files, task_list)
        fallback_files = structured_failed_files or _extract_affected_files(result.log, task_list)

        try: 
            triage = _triage_failure(
                client=client,
                config=config,
                validation_log=result.log,
                task_list=task_list,
                validation_report_json=result.to_json(),
            )
        except Exception as exc: 
            triage = {
                "failures": [
                    {
                        "test": "triage_failed",
                        "classification": "unclear",
                        "affected_files": fallback_files,
                        "reason": f"Triage failed: {exc}",
                        "recommended_action": "Fallback to filename-based repair.",
                    }
                ]
            }

        triage_json = json.dumps(triage,indent=2)
        
        artifacts.save(
            artifacts_dir,
            f"triage/attempt_{attempt}.json",
            triage_json
        )

        affected_files, dependency_issues = _affected_files_from_triage(triage,task_list,fallback_files)

        if dependency_issues and not affected_files:
            dependency_report = json.dumps(
                {
                    "status": "blocked",
                    "reason": "dependency_issue",
                    "required_packages": logic.get("packages", []),
                    "failures": dependency_issues,
                },
                indent=2,
            )

            artifacts.save(
                artifacts_dir,
                f"validation/attempt_{attempt}/dependency_report.json",
                dependency_report,
            )

            artifacts.save(
                artifacts_dir,
                "validation/result.txt",
                "blocked_by_dependency",
            )

            reasons = [
                failure.get("reason", "Unknown dependency failure")
                for failure in dependency_issues
            ]

            return (
                "Paper-to-code generation stopped because required dependencies "
                "are unavailable.\n"
                f"Required packages: {', '.join(logic.get('packages', [])) or 'unknown'}\n"
                f"Reasons: {'; '.join(reasons)}\n"
                f"Artifacts saved to: {artifacts_dir}"
            )

        repair_log = _build_validation_log_with_report(result,triage_json)
        print(
            "Validation failed; repairing "
            f"{len(affected_files)} affected file(s), attempt {attempt}..."
        )

        repaired_files = best_files.copy()

        for filename in affected_files:
            raw = _llm(
                client,
                config,
                prompts.REPAIR_SYSTEM,
                prompts.repair_prompt(
                    paper_text,
                    overall_plan,
                    success_criteria_raw,
                    logic_raw,
                    filename,
                    best_files[filename],
                    repair_log,
                    repaired_files,
                )
            )

            repaired = _extract_code(raw)
            repaired_files[filename] = repaired

            artifacts.save(
                artifacts_dir,
                f"repair/attempt_{attempt}/{filename}.txt",
                repaired,
            )

        current_files = repaired_files

        _save_files_artifact(artifacts_dir,"candidate_code",current_files,)
        _save_files_artifact(artifacts_dir, f"candidate_snapshots/attempt_{attempt}", current_files)

    current_files = best_files

    _write_files(output_dir,current_files) 
    validation_status = "passed" if validation_ok else ("stalled" if stalled else "failed")
    stuck = sorted(s for s in (best_signature or set()) if s.startswith(("FAILED", "ERROR")))
    stuck_section = ("Unresolved tests:\n" + "\n".join(f"  - {s}" for s in stuck) + "\n") if stuck else ""

    packages = logic.get("packages", [])
    package_list = ", ".join(packages) if packages else "none listed"

    return (
        f"Generated {len(task_list)} files in {output_dir}\n"
        f"Validation: {validation_status}\n"
        f"Required packages: {package_list}\n"
        f"{stuck_section}"
        f"Artifacts saved to: {artifacts_dir}"
    )
