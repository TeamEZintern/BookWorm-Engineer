READ_FILE_SCHEMA = {
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
        },
    },
}

WRITE_FILE_SCHEMA = {
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
}

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

SHELL_TIMEOUT = 10

BANNED_COMMAND_PREFIXES = [
    "cd",
    "sudo",
    "git clean"
]

BASH_SCHEMA = {
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
}

ASK_USER_SCHEMA = {
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

SEARCH_SOURCES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_sources",
        "description": (
            "Search the RAG index (ChromaDB) built from the configured sources directory for relevant context. "
            "Use this before answering any question about source documents, research papers, "
            "project notes, or uploaded files. Always cite the source labels returned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant content from indexed sources."
                }
            },
            "required": ["query"]
        }
    }
}

PAPER_TO_CODE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "paper_to_code",
        "description": (
            "Generate a complete code repository from a research paper PDF. "
            "Runs a multi-stage pipeline: planning, analysis, then coding. "
            "Use this when the user wants to implement or reproduce a research paper. "
            "The generated files are written to output_dir."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "paper_path": {
                    "type": "string",
                    "description": "Relative path to the research paper PDF file.",
                },
                "output_dir": {
                    "type": "string",
                    "description": (
                        "Relative path to the directory where the generated code will be written. "
                        "Defaults to {paper_name}_repo if omitted."
                    ),
                },
            },
            "required": ["paper_path"],
        },
    },
}

SCHEMA = [
    READ_FILE_SCHEMA,
    WRITE_FILE_SCHEMA,
    BASH_SCHEMA,
    ASK_USER_SCHEMA,
    SEARCH_SOURCES_SCHEMA,
    PAPER_TO_CODE_SCHEMA,
]