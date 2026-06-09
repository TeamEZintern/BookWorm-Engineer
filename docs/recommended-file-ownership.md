# Recommended File Ownership

## `bookworm/cli.py`

Owned by startup and packaging maintainers.

Change this when:

* adding a new app startup dependency
* changing how `.env` is loaded
* changing CLI entry behavior
* adding flags or command-line arguments later

---

## `bookworm/config.py`

Owned by configuration maintainers.

Change this when:

* adding env vars
* validating settings
* changing defaults
* adding config-derived values

---

## `bookworm/llm.py`

Owned by LLM/provider maintainers.

Change this when:

* changing OpenRouter/OpenAI setup
* adding provider headers
* changing model defaults
* adding retry behavior
* adding provider switching

---

## `bookworm/prompts.py`

Owned by prompt/application behavior maintainers.

Change this when:

* changing system prompt text
* adding `AGENTS.md` or `PROGRESS.md` handling
* adding project memory
* changing instruction formatting

---

## `bookworm/agent.py`

Owned by runtime orchestration maintainers.

Change this when:

* changing the conversation loop
* changing tool-call handling
* changing context usage tracking
* changing model response handling
* changing how assistant output is displayed

---

## `bookworm/commands.py`

Owned by command maintainers.

Change this when:

* adding a new special command (e.g. `init`, `exit`, `mode switch`)
* changing the command dispatch logic in `handle_command`
* changing how commands return results (`CommandResult` variants)
* updating the help text or help command

---

## `bookworm/tools/schema.py`

Owned by tool interface maintainers.

Change this when:

* adding a new tool
* changing tool arguments
* changing tool descriptions

---

## `bookworm/tools/implementation.py`

Owned by tool behavior maintainers.

Change this when:

* changing actual local tool behavior
* changing file handling
* changing shell execution
* changing user input handling

---

## `bookworm/tools/registry.py`

Owned by tool integration maintainers.

Change this when:

* adding a new implementation to the registry
* renaming a tool
* changing how tools receive config

---
