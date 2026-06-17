# BookWorm Engineer — AGENTS.md

## Entrypoints

- `bookworm` (or `python -m bookworm`) — start the agent
- `bookworm index` — rebuild RAG index from sources
- `python -m bookworm.cli` — alternative entry
- **DO NOT** use `python agent.py` or `python cli.py` — those files don't exist at repo root

## Prerequisites

- `.env` file in repo root with at minimum `LLM_API_KEY` (OpenRouter key)
- See `.env.example` for all optional config keys
- Python >= 3.10, install with `pip install -e .`

## Internal Commands (type at `> ` prompt)

| Command | Action |
|---|---|
| `init` | Create `.bookworm/sources/` and `.bookworm/index/` in project |
| `mode switch <plan\|build\|research>` | Change agent mode |
| `exit` / `quit` | Exit agent |
| `help` | Show command list |

## Modes

- **plan** — analyse, ask clarifying Qs, design before coding
- **build** — implement code and run commands
- **research** — answer grounded in indexed sources, always cite source labels

## Architecture

`bookworm.cli:main` → creates `OpenAI` client (OpenRouter) + `ToolRegistry` + `Agent`

### Tools (5 total, registered in `tools/`)

| Tool | Purpose | Key constraint |
|---|---|---|
| `read_file` | Read a file | Relative path only, locked to working dir |
| `write_file` | Write a file | Auto-creates parent dirs |
| `bash` | Run shell commands | Allowlist-only (see below), 10s timeout |
| `ask_user` | Ask user a question | Blocking input |
| `search_sources` | Query RAG index | Requires `bookworm index` first |

### Bash allowlist (`tools/schema.py:58-73`)

`python`, `pip`, `pip3`, `mkdir`, `cp`, `mv`, `rm`, `echo`, `pytest`, `git`, `type`, `dir`, `.\\venv\\Scripts\\activate`

### Bash banlist (`tools/schema.py:77-81`)

`cd`, `sudo`, `git clean`

**Note:** `cd` is banned — the working dir is locked to the project root. Use absolute paths instead.
**Note:** `shell=True` is used — compound commands and pipes work, but splitting must be valid.

## Environment

- `.env` is loaded from **repo root** (two levels up from `bookworm/cli.py`)
- Config is a **frozen dataclass** — all values set at startup from env vars
- Bash subprocess receives a **minimal env**: only `PATH`, `SYSTEMROOT`, `TEMP`, `TMP`, and vars starting with `CONDA_`, `PYTHON`, or `VIRTUAL_ENV`
- `reasoning_effort` is hardcoded to `"low"` in `agent.py:112` — not configurable

## Git workflow

Commit all changes. No remote push (local commits only).

## Testing

```bash
pytest                          # all tests (cacheprovider disabled by default)
pytest tests/test_cli.py        # single file
pytest -p no:cacheprovider      # explicit cache disable (already default in pyproject.toml)
```

Tests live in `tests/`. No fixtures, no integration test prerequisites, no snapshot workflows.

## Files auto-loaded into system prompt

`AGENTS.md` is read from the **project working dir** and injected into the system prompt. Optional — missing file produces empty string.

## Context window

75% usage triggers a system warning to conclude the loop. Threshold at `agent.py:12` (`HALLUNCINATION_THRESHOLD = 0.75`). Default context window is 128,000 tokens.

## .gitignore highlights

`.vscode/`, `.env`, `__pycache__/`, `venv/`, `*.egg-info/`, `reference/`, test tmp dirs excluded.
