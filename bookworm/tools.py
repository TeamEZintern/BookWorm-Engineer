import os
import shlex
import subprocess

WORKING_DIR = os.environ["WORKING_DIR"]

# ---------------------------------------------------------------------------
# Tool definitions — explicit JSON schema passed to the client.
# See: https://openrouter.ai/docs/client-sdks/python/api-reference/chat
# ---------------------------------------------------------------------------

# Command prefixes the agent is allowed to run.
# Extend this list only when a new capability is genuinely needed.
# References:
# - Least-privilege subprocess design: https://securecodingpractices.com/prevent-command-injection-python-subprocess/
# - Least-privilege for coding agents: https://arxiv.org/abs/2605.14859
ALLOWED_COMMAND_PREFIXES = [
    "python",
    "pip",
    "pip3",
    "mkdir",
    "cp",
    "mv",
    "rm",
    "echo",
    "pytest",
    "git",
    "type",
    "dir",
    "git",
    ".\\venv\\Scripts\\activate"
]

BANNED_COMMAND_PREFIXES = [
    "cd",
    "sudo",
    "git clean"
]


SHELL_TIMEOUT = 30  # seconds — kills runaway processes

schema: list = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents. Always use a relative file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "The relative path of the file to read. "
                            "Example: 'src\\file.py'. "
                            "Never use an absolute path."
                        )
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file, creating directories as needed. "
                "Always use this tool to save code — never output code in your reply. "
                "Both file_path and content are required — never call this tool without both."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "The relative path of the file to write. "
                            "Example: 'src\\file.py'. "
                            "Never use an absolute path."
                        )
                    },
                    "content": {
                        "type": "string",
                        "description": "The full file content to write."
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": (
                "Run a shell command with least-privilege restrictions. "
                "Use this for installing packages, running scripts, and inspecting the filesystem. "
                f"Permitted commands: {', '.join(ALLOWED_COMMAND_PREFIXES)}. "
                f"Banned commands: {', '.join(BANNED_COMMAND_PREFIXES)}. "
                "Working directory is locked to the project root. "
                "Do not use this to read or write files. Instead, use read_file or write_file respectfully."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The shell command to run. "
                            "Examples: 'pip install pygame', 'python src\\pong_game.py', 'dir src\\'."
                        )
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": (
                "When in doubt about a high-level decision (e.g. what framework should be used), you can consult the user. "
                "Ask instead of guessing what to do. "
                "Returns the user response."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The question you want to ask the user about. "
                            "You can describe the high-level decision, possible choices, and possible outcomes."
                        )
                    }
                },
                "required": ["question"]
            }
        }
    }
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(file_path: str) -> str:
    try:
        with open(os.path.join(WORKING_DIR, file_path), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def write_file(file_path: str, content: str) -> str:
    abs_file_path = os.path.join(WORKING_DIR, file_path)
    os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written to {file_path}"

def bash(command: str) -> str:
    """Run a shell command with least-privilege restrictions.

    Restrictions applied:
    - Only commands whose first token matches ALLOWED_COMMAND_PREFIXES are permitted.
    - Working directory is locked to WORKING_DIR (set by .env file).
    - Execution times out after SHELL_TIMEOUT seconds.
    - Environment is minimal — only essential host vars are inherited.

    References:
    - https://securecodingpractices.com/prevent-command-injection-python-subprocess/
    - https://docs.python.org/3/library/subprocess.html
    - https://arxiv.org/abs/2605.14859
    """
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
            cwd=WORKING_DIR,              # locked to project root by caller
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
    print("*** Agent Asks ***:\n" + question, end="\n\n")
    user_response = input("*** User response ***:\n").strip()
    print("\n")
    return user_response

available_functions = {
    "read_file":  read_file,
    "write_file": write_file,
    "bash":       bash,
    "ask_user": ask_user,
}