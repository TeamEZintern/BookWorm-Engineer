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

FIX_SYSTEM = (
    "You are an expert software engineer fixing a bug in generated code. "
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
        '  "task_list": ordered list of filenames to implement (dependencies first)\n'
        '  "logic": mapping of filename to a description of its key functions and data flow'
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
        "Return the full file content inside a ```python``` block."
    )


def fix_prompt(filename: str, code: str, error: str) -> str:
    return (
        f"The file `{filename}` has an error.\n\n"
        f"Current content:\n```python\n{code}\n```\n\n"
        f"Error:\n{error}\n\n"
        "Fix the error and return the complete corrected file content."
    )
