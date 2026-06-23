PLANNING_SYSTEM = (
    "You are an expert research engineer. "
    "Analyze the research paper and plan a complete, runnable implementation."
)

SUCCESS_CRITERIA_SYSTEM = (
    "You are an expert research reproducibility engineer. "
    "Extract concrete, testable success criteria from a research paper. "
    "Return only one complete, valid JSON object without Markdown fences."
)

ARCHITECTURE_SYSTEM = (
    "You are an expert software architect. "
    "Return only one complete, valid JSON object without Markdown fences or "
    "explanatory text. Ensure every array and object is closed."
)

ANALYSIS_SYSTEM = (
    "You are an expert software engineer. "
    "Analyze how a specific file should be implemented before code is written."
)

CODING_SYSTEM = (
    "You are an expert software engineer implementing research code. "
    "Write complete, runnable Python files. "
    "Return only the file content inside a ```python``` block."
)

TRIAGE_SYSTEM = (
    "You are an expert software validation triage assistant. "
    "Classify failed validation checks before code repair. "
    "Validation checks may include compileall, import smoke tests, Ruff "
    "linting, and pytest. Return only one complete, valid JSON object."
)

REPAIR_SYSTEM = (
    "You are an expert software engineer repairing generated research code. "
    "Return only the complete corrected file content inside a ```python``` block."
    "Do not introduce new lint errors or unused varables; use raw strings (r\"...\") for any regex"
    "Do not break tests that currently pass."
)


def overall_plan_prompt(paper_text: str) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Create a detailed plan to reproduce the implementation described in "
        "this paper. Cover the core algorithm or model, experimental setup, "
        "and key components required."
    )


def success_criteria_prompt(paper_text: str, overall_plan: str) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall implementation plan:\n"
        f"{overall_plan}\n\n"
        "Extract success criteria that can validate the generated "
        "implementation. Separate deterministic unit-test criteria from "
        "optional, expensive reproducibility criteria.\n\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        '  "unit_test_criteria": [\n'
        "    {\n"
        '      "id": "C1",\n'
        '      "claim": "...",\n'
        '      "expected_behavior": "...",\n'
        '      "test_strategy": "...",\n'
        '      "source_section": "...",\n'
        '      "confidence": "high | medium | low"\n'
        "    }\n"
        "  ],\n"
        '  "reproducibility_criteria": [\n'
        "    {\n"
        '      "id": "R1",\n'
        '      "metric": "...",\n'
        '      "reported_value": "...",\n'
        '      "dataset": "...",\n'
        '      "evaluation_protocol": "...",\n'
        '      "required_compute": "small | medium | large | unknown",\n'
        '      "source_section": "...",\n'
        '      "confidence": "high | medium | low"\n'
        "    }\n"
        "  ],\n"
        '  "unverifiable_claims": [\n'
        "    {\n"
        '      "claim": "...",\n'
        '      "reason": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Do not invent results not stated in the paper.\n"
        "- Prefer criteria that can become deterministic pytest tests.\n"
        "- Put large training runs under reproducibility_criteria.\n"
        "- Put vague or underspecified claims under unverifiable_claims.\n"
        "- Return JSON only and close every array and object."
    )


def architecture_prompt(
    paper_text: str,
    overall_plan: str,
    success_criteria: str,
) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Paper-derived success criteria:\n"
        f"{success_criteria}\n\n"
        "Design the software architecture.\n\n"
        "Return exactly one complete JSON object with this shape:\n"
        "{\n"
        '  "files": [\n'
        "    {\n"
        '      "name": "relative/path.py",\n'
        '      "description": "purpose"\n'
        "    }\n"
        "  ],\n"
        '  "dependencies": {\n'
        '    "relative/path.py": ["dependency.py"]\n'
        "  }\n"
        "}\n\n"
        "Rules:\n"
        "- Return JSON only, without Markdown fences or commentary.\n"
        "- Close every array and object, including the outer JSON object.\n"
        "- Include implementation files and pytest files.\n"
        "- All filenames must be relative paths ending in .py.\n"
        "- Pytest files must be under tests/ and named test_<module>.py.\n"
        "- Put production code only in implementation files.\n"
        "- Put tests, fixtures, and assertions only in test files.\n"
        "- Add feasible deterministic tests for relevant unit-test criteria.\n"
        "- Tests must not require network access, GPUs, large datasets, or "
        "long training runs.\n"
        "- Include a main entry point."
    )


def logic_design_prompt(
    paper_text: str,
    overall_plan: str,
    architecture: str,
    success_criteria: str,
) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Paper-derived success criteria:\n"
        f"{success_criteria}\n\n"
        "Architecture:\n"
        f"{architecture}\n\n"
        "Design the implementation logic.\n\n"
        "Return exactly one complete JSON object with these keys:\n"
        '- "packages": list of required pip package names\n'
        '- "task_list": ordered list of filenames, dependencies first\n'
        '- "logic": mapping of filename to key functions and data flow\n\n'
        "Rules:\n"
        "- Return JSON only and close every array and object.\n"
        "- List implementation files before the pytest files that test them.\n"
        "- Keep tests under tests/.\n"
        "- Do not put tests inside implementation modules.\n"
        "- Tests should cover deterministic behavior, shapes, edge cases, "
        "smoke checks, and feasible unit-test criteria.\n"
        "- Avoid network access, GPUs, large datasets, long training runs, and "
        "exact reproduction of stochastic metrics."
    )


def analysis_prompt(
    paper_text: str,
    overall_plan: str,
    architecture: str,
    logic_design: str,
    filename: str,
    file_description: str,
    success_criteria: str,
) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Paper-derived success criteria:\n"
        f"{success_criteria}\n\n"
        "Architecture:\n"
        f"{architecture}\n\n"
        "Logic design:\n"
        f"{logic_design}\n\n"
        f"Analyze how to implement `{filename}` ({file_description}). "
        "Describe its classes and functions, data flow, algorithms, public "
        "interfaces, dependencies, and edge cases. Do not write code yet."
    )


def coding_prompt(
    paper_text: str,
    overall_plan: str,
    success_criteria: str,
    logic_design: str,
    filename: str,
    file_analysis: str,
    prior_files: dict[str, str],
) -> str:
    prior = "\n\n".join(
        f"# {name}\n```python\n{code}\n```"
        for name, code in prior_files.items()
    )
    prior_section = (
        f"Previously implemented files:\n\n{prior}\n\n"
        if prior
        else ""
    )

    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Paper-derived success criteria:\n"
        f"{success_criteria}\n\n"
        "Logic design:\n"
        f"{logic_design}\n\n"
        f"{prior_section}"
        f"Analysis for `{filename}`:\n"
        f"{file_analysis}\n\n"
        f"Implement `{filename}` completely.\n\n"
        "Rules:\n"
        f"- If `{filename}` is under tests/, write pytest tests only.\n"
        f"- If `{filename}` is not under tests/, write production code only.\n"
        "- Do not put pytest imports, test functions, unittest classes, "
        "fixtures, or assertion-based unit tests in production files.\n"
        "- Test deterministic behavior, shapes, edge cases, and smoke paths.\n"
        "- Do not require network access, GPUs, large datasets, or long runs.\n"
        "- Do not add a test-running __main__ block.\n"
        "- A planned entry point may include a minimal guarded CLI or demo.\n"
        "- Return the full file content inside one ```python``` block."
    )


def triage_prompt(
    validation_log: str,
    task_list: list[str],
    validation_report_json: str | None = None,
) -> str:
    files = "\n".join(f"- {filename}" for filename in task_list)

    structured_report = ""
    if validation_report_json:
        structured_report = (
            "Structured validation report:\n"
            "```json\n"
            f"{validation_report_json}\n"
            "```\n\n"
        )

    return (
        "Classify every failed validation check.\n\n"
        "Checks may include:\n"
        "- compileall: Python syntax errors\n"
        "- import_smoke: import-time failures\n"
        "- ruff_autofix: deterministic Ruff fixes\n"
        "- ruff: remaining lint failures\n"
        "- pytest: test collection or execution failures\n\n"
        "Valid classifications:\n"
        "- syntax_error\n"
        "- import_error\n"
        "- lint_issue\n"
        "- implementation_bug\n"
        "- test_bug\n"
        "- dependency_issue\n"
        "- unclear\n\n"
        "Known project files:\n"
        f"{files}\n\n"
        f"{structured_report}"
        "Validation log:\n"
        "```text\n"
        f"{validation_log}\n"
        "```\n\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        '  "failures": [\n'
        "    {\n"
        '      "check": "compileall | import_smoke | ruff_autofix | ruff | '
        'pytest | unknown",\n'
        '      "classification": "syntax_error | import_error | lint_issue | '
        'implementation_bug | test_bug | dependency_issue | unclear",\n'
        '      "affected_files": ["..."],\n'
        '      "reason": "...",\n'
        '      "recommended_action": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Return JSON only and close every array and object.\n"
        "- Missing external packages are dependency_issue.\n"
        "- Only include filenames from the known project-file list.\n"
        "- Prefer filenames explicitly present in the structured report.\n"
        "- Use an empty affected_files list when the files are unclear."
    )


def repair_prompt(
    paper_text: str,
    overall_plan: str,
    success_criteria: str,
    logic_design: str,
    filename: str,
    current_code: str,
    validation_log: str,
    prior_files: dict[str, str],
) -> str:
    prior = "\n\n".join(
        f"# {name}\n```python\n{code}\n```"
        for name, code in prior_files.items()
        if name != filename
    )
    prior_section = f"Other current files:\n\n{prior}\n\n" if prior else ""

    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Paper-derived success criteria:\n"
        f"{success_criteria}\n\n"
        "Logic design:\n"
        f"{logic_design}\n\n"
        f"{prior_section}"
        "Validation failed with this log and structured report:\n"
        "```text\n"
        f"{validation_log}\n"
        "```\n\n"
        f"Current content of `{filename}`:\n"
        "```python\n"
        f"{current_code}\n"
        "```\n\n"
        f"Repair `{filename}` so the project passes validation.\n\n"
        "Rules:\n"
        "- Return the complete corrected file, not a patch.\n"
        "- Preserve the intended algorithm and public interfaces.\n"
        "- Keep changes focused on the reported failure.\n"
        "- Do not remove meaningful tests merely to make validation pass.\n"
        "- Do not add network access, GPU requirements, large datasets, or "
        "long-running code.\n"
        "- Production files must not contain pytest tests.\n"
        "- Test files must remain pytest-compatible.\n"
        "- Return the complete file inside one ```python``` block."
    )
