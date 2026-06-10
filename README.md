# BookWorm-Engineer

An AI Agent inspired by NotebookLM for processing sources and opencode for being a CLI agent assistant.

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd BookWorm-Engineer

# 2. Install the package (creates the `bookworm` command)
pip install -e . --config-settings editable_mode=compat

# 3. Create a .env file in the repo root (see .env.example or copy from a teammate)
```

## Usage

Run `bookworm` from any project directory:

```bash
cd /path/to/your/project
bookworm
```

The `WORKING_DIR` is set automatically to your current directory — no need to configure it.

### First-time setup

If `bookworm` is not found on your PATH, add your Python Scripts directory:
```bash
# Windows (conda)
C:\Users\<you>\miniconda3\Scripts
```

### Running without the `bookworm` command

```bash
python -m bookworm
# or
python agent.py
```

## Dependencies

- Python >= 3.10
- See `requirements.txt` or `pyproject.toml` for the full list.