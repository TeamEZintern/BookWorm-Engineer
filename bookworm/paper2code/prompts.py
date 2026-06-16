PLANNING_SYSTEM = (
    "You are an expert research engineer. "
    "Your task is to analyze a research paper and plan a complete, runnable implementation."
)

ANALYSIS_SYSTEM = (
    "You are an expert software engineer. "
    "Your task is to analyze how a specific file should be implemented before any code is written."
)

CODING_SYSTEM = (
    "You are an expert software engineer implementing research code. "
    "Write complete, runnable Python files. Return only the file content inside a ```python``` block."
)

TRIAGE_SYSTEM = (
    "You are an expert software engineer test triage assistant. "
    "Classify validation failures before code repair. "
    "Return only valid JSON. "
)

REPAIR_SYSTEM = (
    "You are an expert software engineer repairing generated research code. "
    "Return only the complete corrected file content inside a ```python``` block."
)


def overall_plan_prompt(paper_text: str) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Create a detailed plan to reproduce the implementation described in this paper. "
        "Cover: the core algorithm or model, the experimental setup, and the key components needed."
    )


def architecture_prompt(paper_text: str, overall_plan: str) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Design the software architecture. "
        "Return a JSON object with exactly these keys:\n"
        '  "files": list of {"name": filename, "description": purpose}\n'
        '  "dependencies": mapping of filename to list of filenames it imports from\n'
        "Separate implementation files from test files."
        "Pytest files must live under tests/ and be named test_<module>.py."
        "Do not place unit tests, pytest functions, unittest classes, test fixtures, or __main__ test blocks inside implementation files."
        "Return implementation files and test files separately in the architecture. Include pytest tests for core behaviour."
        'The "files" list must include both implementation files and pytest files.'
        "Test files must use names like tests/test_model.py."
        "All files must be Python (.py). Include a main entry point."
    )


def logic_design_prompt(paper_text: str, overall_plan: str, architecture: str) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Architecture:\n"
        f"{architecture}\n\n"
        "Design the implementation logic. "
        "Return a JSON object with exactly these keys:\n"
        '  "packages": list of pip package names required\n'
        '  "task_list": ordered list of filenames to implement (dependencies first) and pytest files after the implementation files they test\n'
        '  "logic": mapping of filename to a description of its key functions and data flow'
        'The "task_list" must list implementation files first, then pytest files under tests/.'
        "Tests should depend on the implementation files they test."
        "Do not include inline tests in implementation modules"
        "All pytest test functions, fixtures, assertions, and test helpers must be placed in tests/ files only."
    )


def analysis_prompt(
    paper_text: str,
    overall_plan: str,
    architecture: str,
    logic_design: str,
    filename: str,
    file_description: str,
) -> str:
    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Architecture:\n"
        f"{architecture}\n\n"
        "Logic design:\n"
        f"{logic_design}\n\n"
        f"Analyze how to implement `{filename}` ({file_description}). "
        "Describe: key classes and functions, data flow, algorithms used, and edge cases to handle. "
        "Do not write code yet."
    )


def coding_prompt(
    paper_text: str,
    overall_plan: str,
    logic_design: str,
    filename: str,
    file_analysis: str,
    prior_files: dict[str, str],
) -> str:
    prior = "\n\n".join(
        f"# {name}\n```python\n{code}\n```" for name, code in prior_files.items()
    )
    prior_section = f"Previously implemented files:\n\n{prior}\n\n" if prior else ""

    return (
        "Here is a research paper:\n\n"
        f"{paper_text}\n\n"
        "Overall plan:\n"
        f"{overall_plan}\n\n"
        "Logic design:\n"
        f"{logic_design}\n\n"
        f"{prior_section}"
        f"Analysis for `{filename}`:\n"
        f"{file_analysis}\n\n"
        f"Implement `{filename}` completely. "
        "If this filename is a pytest file, implement meaningful pytest for the corresponding module."
        "Tests should focus on deterministic behavior, input/output shapes, edge cases, and smoke checks."
        "Avoid tests that require network access, large datasets, GPUs, or long training runs."
        f"""Testing rules:
- If `{filename}` is under `tests/`, write pytest tests only.
- If `{filename}` is not under `tests/`, write production implementation only.
- Do not include pytest imports, test_* functions, unittest.TestCase classes, fixtures, or assertion-based unit tests in production files.
- Do not add `if __name__ == "__main__"` blocks for running tests.
- Production files may include a minimal CLI/demo main only if this file is the planned entry point.
"""
        "Return the full file content inside a ```python``` block."
    )

def triage_prompt(
    validation_log: str,
    task_list: list[str],
) -> str:
    
    files = "\n".join(f"- {filename}" for filename in task_list)

    return (
        "Classify each pytest failure in this validation log.\n\n"
        "Valid classifications:\n"
        "- implementation_bug\n"
        "- test_bug\n"
        "- dependency_issue\n"
        "- unclear\n\n"
        "Known project files:\n"
        f"{files}\n\n"
        "Validation log:\n"
        f"```text\n{validation_log}\n```\n\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        '  "failures": [\n'
        "    {\n"
        '      "test": "...",\n'
        '      "classification": "implementation_bug | test_bug | dependency_issue | unclear",\n'
        '      "affected_files": ["..."],\n'
        '      "reason": "...",\n'
        '      "recommended_action": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Only include files from the known project files list in affected_files.\n"
        "- If the implementation is wrong, classify as implementation_bug.\n"
        "- If the test expectation is wrong or brittle, classify as test_bug.\n"
        "- If the failure is caused by a missing package or environment issue, classify as dependency_issue.\n"
        "- If there is not enough evidence, classify as unclear.\n"
        "- Return JSON only."
    )

def repair_prompt(
    paper_text: str,
    overall_plan: str,
    logic_design: str,
    filename: str,
    current_code: str,
    validation_log: str,
    prior_files: dict[str, str],
) -> str:
    prior = "\n\n".join(
        f" # {name}\n```python```\n{code}\n```"
        for name, code in prior_files.items()
        if name != filename
    )
    prior_section = f"Other current files:\n\n{prior}\n\n"

    return (
        f"""
Here is a research paper:\n\n{paper_text}\n\n

Overall plan:\n {overall_plan}\n\n

Logic desgin:\n{logic_design}\n\n

{prior_section}

Validation failed with this log:\n```text\n{validation_log}\n```\n\n

Current content of `{filename}`:\n```python\n{current_code}\n```\n\n

Repair `{filename}` so the project passes validation.

Preserve the intended algorithm and public interfaces.

Return the full corrected file content inside a ```python``` block.
"""
    )