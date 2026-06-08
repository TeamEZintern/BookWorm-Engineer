from pathlib import Path

from .config import Config

def _read_optional_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
      return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
 
    
def build_system_prompt(config: Config, mode: str = "plan") -> str:
    agents_md = _read_optional_file(config.working_dir / "AGENTS.md")
    progress_md = _read_optional_file(config.working_dir / "PROGRESS.md")

    mode_behaviour = {
        "plan": (
            "You are in Plan mode. Analyse the request, ask clarifying questions, "
            "and design a solution before writing any code."
        ),
        "build": (
            "You are in Build mode. Implement code and run commands. "
            "Once a feature is complete: append to PROGRESS.md, then commit all changes to git."
        ),
        "research": (
            "You are in Research mode. Answer questions grounded in loaded sources. "
            "Always cite the source (and page number if applicable)."
        ),
    }

    system_prompt = f"""You are BookWorm Engineer, a research-grounded coding assistant.
Working Directory: {config.working_dir}
Current mode: {mode.capitalize()}

{mode_behaviour.get(mode, "")}

Initialize git config with these commands:
> git config --global user.name "{config.git_user_name}"
> git config --global user.email "{config.git_user_email}"

You must initialize the correct environment for the project (e.g. venv). This is to ensure dependencies are installed correctly (i.e. "pip install ...").

Once a feature is completed you must do these before trying to implement the next feature:
> Append to and clean up PROGRESS.md with tool updates.
> Commit all changes to the local git repository with an appropriate message using the 'bash' tool.
  > No need to push to remote.
  > IMPORTANT: Always stage changes of PROGRESS.md BEFORE committing to git.

### HIGH-LEVEL DIRECTORY RULES (AGENTS.md)
{agents_md}

### RUNTIME CONTINUITY STATE (PROGRESS.md)
{progress_md}

OPERATING MANDATE:
1. Review user tasks alongside the rigid guardrails outlined in AGENTS.md.
2. If building files, you MUST run verification commands listed under AGENTS.md via the 'bash' tool to ensure compliance.
3. Prior to concluding your processing loop you must remember to update PROGRESS.md and commit changes to Git again.
"""
    return system_prompt

