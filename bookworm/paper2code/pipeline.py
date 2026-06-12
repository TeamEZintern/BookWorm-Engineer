import json
import re
from pathlib import Path

from openai import OpenAI

from ..config import Config
from . import artifacts, prompts
from .pdf import extract_text


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
        output_path = output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")

    packages = logic.get("packages", [])
    package_list = ", ".join(packages) if packages else "none listed"

    return (
        f"Generated {len(task_list)} files in {output_dir}\n"
        f"Required packages: {package_list}\n"
        f"Artifacts saved to: {artifacts_dir}"
    )
