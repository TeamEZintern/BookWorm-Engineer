# Quick Reference Table

| Area                 | File                               | Main API                                      | Purpose                                            |
| -------------------- | ---------------------------------- | --------------------------------------------- | -------------------------------------------------- |
| CLI startup          | `bookworm/cli.py`                  | `main()`                                      | Starts the app and wires dependencies              |
| Config               | `bookworm/config.py`               | `load_config()` / `Config`                    | Reads and validates runtime settings               |
| LLM client           | `bookworm/llm.py`                  | `create_client()`                             | Creates OpenAI-compatible client                   |
| Prompt               | `bookworm/prompts.py`              | `build_system_prompt()`                       | Builds system prompt from config and project files |
| Agent runtime        | `bookworm/agent.py`                | `Agent.run()`                                 | Runs conversation loop and tool calls              |
| Tool registry        | `bookworm/tools/registry.py`       | `create_tool_registry()`                      | Binds schemas to implementations                   |
| Tool schemas         | `bookworm/tools/schema.py`         | `SCHEMA`                                      | Defines tools visible to the LLM                   |
| Tool implementations | `bookworm/tools/implementation.py` | `read_file`, `write_file`, `bash`, `ask_user` | Implements local capabilities                      |
| Console command      | `pyproject.toml`                   | `bookworm = "bookworm.cli:main"`              | Allows running `bookworm`                          |
| Module command       | `bookworm/__main__.py`             | `main()`                                      | Allows running `python -m bookworm`                |

---
