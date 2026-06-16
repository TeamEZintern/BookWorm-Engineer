import json
import re
from pathlib import Path

from openai import OpenAI

from ..config import Config
from . import artifacts, prompts
from .pdf import extract_text
from .validation import _load_validated_or_initial_code,_run_validation

MAX_VALIDATION_ATTEMPTS = 3

def _llm(client: OpenAI, config: Config, system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=config.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


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


def _extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text

def _write_files(output_dir: Path, files: dict[str, str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, code in files.items():
        output_path = output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")

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
) -> dict:
    raw = _llm(
        client,
        config,
        prompts.TRIAGE_SYSTEM,
        prompts.triage_prompt(validation_log, task_list)
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

    return list(dict.fromkeys(matched))

def _affected_files_from_triage(
        triage: dict,
        task_list: list[str],
        fallback_files: list[str],
) -> list[str]:
    affected: list[str] = []

    for failure in triage.get("failures", []):
        classification = failure.get("classification")
        if classification == "dependency_issue":
            continue

        candidate_files = failure.get("affected_files", [])
        if isinstance(candidate_files, list):
            affected.extend(_match_task_files(candidate_files, task_list))

    affected = list(dict.fromkeys(affected))
    return affected or fallback_files

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

    # Stage 1b: Architecture
    architecture_raw = artifacts.load(artifacts_dir, "architecture.txt")
    if architecture_raw is None:
        print("Planning: architecture...")
        architecture_raw = _llm(
            client, config,
            prompts.PLANNING_SYSTEM,
            prompts.architecture_prompt(paper_text, overall_plan),
        )
        artifacts.save(artifacts_dir, "architecture.txt", architecture_raw)

    try:
        architecture = _extract_json(architecture_raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return f"Failed to parse architecture JSON: {exc}\n\nRaw response:\n{architecture_raw}"

    # Stage 1c: Logic design
    logic_raw = artifacts.load(artifacts_dir, "logic_design.txt")
    if logic_raw is None:
        print("Planning: logic design...")
        logic_raw = _llm(
            client, config,
            prompts.PLANNING_SYSTEM,
            prompts.logic_design_prompt(paper_text, overall_plan, architecture_raw),
        )
        artifacts.save(artifacts_dir, "logic_design.txt", logic_raw)

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

    for attempt in range(1, MAX_VALIDATION_ATTEMPTS + 1):
        _write_files(output_dir, current_files)

        result = _run_validation(output_dir)
        artifacts.save(artifacts_dir, f"validation/attempt_{attempt}.log", result.log)

        if result.ok:
            validation_ok = True
            artifacts.save(artifacts_dir, "validation/result.txt" , "passed")
            break

        if attempt == MAX_VALIDATION_ATTEMPTS:
            artifacts.save(artifacts_dir, "validation/result.txt", "failed")
            break

        fallback_files = _extract_affected_files(result.log, task_list)

        try: 
            triage = _triage_failure(
                client=client,
                config=config,
                validation_log=result.log,
                task_list=task_list,
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

        affected_files = _affected_files_from_triage(triage,task_list,fallback_files)

        repair_log = (
            result.log
            + "\n\n"
            + "Triage report:\n"
            + "```json\n"
            + triage_json
            + "\n```"
        )

        print(
            "Validation failed; repairing "
            f"{len(affected_files)} affected file(s), attempt {attempt}..."
        )

        repaired_files = current_files.copy()

        for filename in affected_files:
            raw = _llm(
                client,
                config,
                prompts.REPAIR_SYSTEM,
                prompts.repair_prompt(
                    paper_text,
                    overall_plan,
                    logic_raw,
                    filename,
                    current_files[filename],
                    repair_log,
                    current_files,
                )
            )

            repaired = _extract_code(raw)
            repaired_files[filename] = repaired
            artifacts.save(
                artifacts_dir,
                f"repair/attempt_{attempt}/{filename}.txt",
                repaired,
            )
            artifacts.save(
                artifacts_dir,
                f"validated_code/{filename}.txt",
                repaired,
            )

        current_files = repaired_files

    _write_files(output_dir,current_files)

    validation_status = "passed" if validation_ok else "failed"

    packages = logic.get("packages", [])
    package_list = ", ".join(packages) if packages else "none listed"

    return (
        f"Generated {len(task_list)} files in {output_dir}\n"
         f"Validation: {validation_status}\n"
        f"Required packages: {package_list}\n"
        f"Artifacts saved to: {artifacts_dir}"
    )
