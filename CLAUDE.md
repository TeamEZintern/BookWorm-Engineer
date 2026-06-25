# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`bookworm-engineer` is a CLI coding/research agent — a tool-calling chat loop over an OpenAI-compatible
LLM (defaults to OpenRouter `openai/gpt-4o-mini`), with a local RAG subsystem and a paper-to-code
pipeline. It is installed as the `bookworm` console command.

## Commands

```bash
pip install -e .            # install the editable package + the `bookworm` console script
bookworm                    # run the agent loop (implicit `chat` subcommand)
bookworm chat               # same as above
bookworm index              # (re)build the ChromaDB RAG index from .bookworm/sources/
python -m bookworm          # run without the console script (same dispatch as cli.main)

pytest                      # run the full test suite (testpaths=tests in pyproject.toml)
pytest tests/test_config.py # run one test file
pytest tests/test_config.py::test_name   # run a single test
ruff check .                # lint
ruff check . --fix          # lint + autofix
```

Requires a `.env` **in the package root** (next to `pyproject.toml`) — `cli.main` calls
`load_dotenv(repo_root / ".env")` where `repo_root` is the package parent, *not* the user's CWD.
Only `LLM_API_KEY` is mandatory; see `.env.example` for the rest. The agent's `working_dir`, however,
is `Path.cwd()` — so `bookworm` operates on whatever directory you launch it from, while reading its
API key from the package's `.env`.

## CWD vs. package root — the key mental model

Two different roots are in play and conflating them causes bugs:

- **Package root** (`Path(__file__).parent.parent` in `cli.py`): only used to locate `.env`.
- **`config.working_dir`** (`Path.cwd()`): the sandbox. All runtime state, file tools, RAG sources,
  and paper2code output resolve relative to this. Everything lives under `<cwd>/.bookworm/`
  (`sources/`, `index/`, `paper2code/<paper>/`). Nothing runtime is ever written inside the package.

## Architecture

`cli.py:main` is the single startup path and the only place wiring happens: load `.env` → `load_config`
→ `create_client` → `create_tool_registry` → `build_system_prompt` → construct `Agent` → `agent.run()`.
The guiding rule is **"imports should be boring, execution should be explicit"** — importing a module
must never load env, create clients, or start the loop. Keep side effects in `main`, not at import time.

Three subsystems share that spine:

### 1. Agent loop (`agent.py`, `commands.py`, `tools/`)
- `Agent.run()` is the REPL; `Agent._run_turn()` is the tool-calling loop: call the LLM with
  `tools=registry.schema`, append the assistant message, dispatch every `tool_call` via `call_tool`,
  append `role:"tool"` results, repeat until the model returns no tool calls.
- Bare-string inputs are first routed through `handle_command` (`commands.py`): `init`, `exit`/`quit`,
  `help`, `mode switch <plan|build|research>`. Only non-commands reach the LLM.
- **Modes change the system prompt, not the toolset.** `_set_mode` rewrites `messages[0]` via
  `build_system_prompt(config, mode)`. The three modes are `plan` (default), `build`, `research`.
- A context-pressure guard injects a "wrap up" system message once `prompt_tokens / context_window`
  crosses `HALLUNCINATION_THRESHOLD` (0.75).

### 2. Tools — the three-part contract
Every tool is **schema + implementation + registry binding**, and all three must stay in sync:
- `tools/schema.py` — the JSON the LLM sees (`SCHEMA` list). Also defines `ALLOWED_COMMAND_PREFIXES`,
  `BANNED_COMMAND_PREFIXES`, and `SHELL_TIMEOUT` (10s).
- `tools/implementation.py` — `create_implementations(config)` returns a `name -> callable` dict via
  closures over `config`. The six tools: `read_file`, `write_file`, `bash`, `ask_user`,
  `search_sources`, `paper_to_code`.
- `tools/registry.py` — `create_tool_registry` bundles schema+impls; `call_tool` parses JSON args,
  dispatches, and converts every failure into a returned error string (the loop never raises on a bad
  tool call).

Adding/changing a tool means editing all three: append to `SCHEMA`, add the closure in
`create_implementations`, and the registry picks it up automatically by name. The dict key in
`create_implementations` **must** equal the schema `function.name`.

**Security model (least privilege):**
- `read_file`/`write_file` resolve through `_resolve_inside_working_dir`, which rejects any path that
  escapes `working_dir` (`is_relative_to` check). Never weaken this.
- `bash` is allow-listed: the command's basename (sans `.exe`) must match `ALLOWED_COMMAND_PREFIXES`,
  runs with a **minimal scrubbed env** (only `PATH`, `SYSTEMROOT`, `TEMP`, `TMP`, plus `CONDA_*`/
  `PYTHON*`/`VIRTUAL_ENV` passthrough) so host credentials aren't leaked, and `cwd` is locked to
  `working_dir`. Extend the allow-list only when genuinely needed.

### 3. RAG (`rag/`)
- `indexer.py:build_index` loads `.txt`/`.md` (one Document each) and `.pdf` (one Document **per page**,
  with `page` metadata) from `rag_sources_dir`, splits via `RecursiveCharacterTextSplitter`, embeds with
  a local HuggingFace MiniLM model (`rag/embeddings.py`), and persists to ChromaDB.
- `retriever.py:retrieve_context` is reached **only** through the `search_sources` tool. Documents
  sitting in ChromaDB are not in the prompt until the model calls that tool — retrieval is model-driven.
- **Known sharp edge:** `Chroma.from_documents` *appends*, so re-running `bookworm index` over an
  existing collection duplicates chunks. There is no dedupe/clear step yet.

### 4. Paper-to-code pipeline (`paper2code/`)
Invoked by the `paper_to_code` tool → `pipeline.run_pipeline`. A staged LLM pipeline where **every stage
is cached to disk** under `.bookworm/paper2code/<paper_name>/` via `artifacts.save`/`artifacts.load`, so a
crashed/interrupted run resumes from the last completed artifact rather than restarting.

Stage order (`pipeline.py`):
1. **Plan** — `overall_plan.txt`
2. **Success criteria** — `success_criteria.json` (derived *before* architecture; later stages consume it)
3. **Architecture** — `architecture.txt` (JSON: file list + descriptions)
4. **Logic design** — `logic_design.txt` (JSON: `task_list`, per-file `logic`, `packages`)
5. **Analysis** — one `analysis/<file>.txt` per file in `task_list`
6. **Coding** — one `code/<file>.txt` per file, in `task_list` (dependency) order, each seeing `prior_files`
7. **Validation + repair** — up to `MAX_VALIDATION_ATTEMPTS` (3)

Validation/repair loop:
- `validation.py:_run_validation` runs **gated** checks; a failed gate skips the rest so a downstream
  "passed" can't mask an upstream break. Order: **compileall → import smoke (impl files only) →
  ruff autofix → ruff JSON lint → pytest** (pytest skipped if no `test_*.py`/`*_test.py` exist).
- On failure, `_triage_failure` asks the LLM to classify each failure; `dependency_issue` failures with
  no repairable files **block** the run (deps can't be installed), otherwise affected files are repaired
  and re-validated.
- Artifacts track provenance honestly: `candidate_code/` = latest repaired attempt;
  `validated_code/` = code that passed the **full** sequence (only promoted via `_promote_validated_code`
  after `result.ok`). Per-attempt snapshots under `validation/attempt_N/` and `repair/attempt_N/`.
- Ruff autofix mutates files on disk, so after each validation the pipeline re-reads task files from
  `output_dir` (`_read_task_files`) to keep its in-memory copy current.
- LLM JSON responses are parsed leniently by `_extract_json` (tries fenced blocks, then outermost
  `{...}`, with a backslash-escape repair pass) because models wrap/format JSON inconsistently.

`paper2code/prompts.py` holds all stage system prompts and prompt builders; `paper2code/pdf.py`
extracts paper text. `pipeline.py` carries no prompt text itself.

## System prompt & external project files

`prompts.py:build_system_prompt` injects, if present in `working_dir`, the contents of **`AGENTS.md`**
(directory rules / guardrails the agent must honor) and **`PROGRESS.md`** (runtime continuity state).
In `build` mode the agent is instructed to append to `PROGRESS.md` and git-commit after each feature.
These files belong to the *user's* project being worked on, not to this repo.

## Conventions

- Config is a frozen dataclass built in one place (`config.py:load_config`); read values off `config`,
  don't call `os.getenv` elsewhere. Env helpers: `_required_env`, `_optional_env`, `_int_env`, `_path_env`
  (relative paths resolve against `working_dir`).
- Tests use `pytest` with `SimpleNamespace` fakes for `Config` and `monkeypatch` for `load_config`/
  `load_dotenv` — no real network or API key needed. Follow that pattern; don't hit the live LLM in tests.
- `.bookworm/`, `.pytest-tmp*`, `__pycache__`, `*.egg-info`, and the `.BookwormEngineer/` venv are
  generated/local — never edit or commit them as source.

## Working style — teach, don't just apply (IMPORTANT)

The owner of this repo is **learning while building**. For any request that would change source code
here, do **not** edit files directly as the default. Instead, in your reply:

1. **Give the plan first** — what you'll change, where (file + function), and *why* (root cause,
   trade-offs, and any decisions that need the owner's input).
2. **Show an implementation example** — the actual code as a snippet in the reply, so the owner can
   read it, understand it, and apply it themselves. Explain the non-obvious parts.
3. **Wait for explicit approval** before using Edit/Write on source files — e.g. "apply it", "make
   the change", "go ahead", "code it out".

Diagnosis, reading files, searching, and running tests/commands do **not** need this gate — only
modifying source files does. When in doubt, present the plan + example and ask before applying.
