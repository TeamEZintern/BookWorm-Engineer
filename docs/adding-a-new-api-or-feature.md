# Adding a New API or Feature

Use this checklist when expanding the project.

## Adding a New Environment Setting

Example: adding `MAX_TOOL_CALLS`.

Steps:

1. Add it to `.env.example`.

```env
MAX_TOOL_CALLS=20
```

2. Add it to `Config`.

```python
max_tool_calls: int
```

3. Parse it in `load_config`.

```python
max_tool_calls=_int_env("MAX_TOOL_CALLS", 20)
```

4. Use it through `config`.

```python
self.config.max_tool_calls
```

Do not read it directly from `os.environ` in `agent.py`.

---

## Adding a New Tool

Example: adding `list_files`.

### Step 1: Add schema in `schema.py`

```python
{
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files inside a directory under the working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path relative to the working directory.",
                }
            },
            "required": ["directory"],
            "additionalProperties": False,
        },
    },
}
```

### Step 2: Add implementation in `implementation.py`

```python
def list_files(directory: str) -> str:
    ...
```

### Step 3: Register it in `registry.py`

```python
implementations={
    "read_file": read_file,
    "write_file": write_file,
    "bash": bash,
    "ask_user": ask_user,
    "list_files": list_files,
}
```

### Step 4: Test that schema name and implementation key match

The schema name:

```python
"name": "list_files"
```

must match:

```python
"list_files": list_files
```

---

## Adding a New LLM Provider

Add provider-specific logic to:

```text
bookworm/llm.py
```

Not to:

```text
bookworm/agent.py
```

Recommended approach:

```python
def create_client(config: Config) -> OpenAI:
    ...
```

Later, this can evolve into:

```python
def create_client(config: Config) -> LLMClientProtocol:
    ...
```

or:

```python
def create_provider(config: Config) -> BaseProvider:
    ...
```

Keep the agent dependent on behavior, not provider-specific setup.

---

## Adding More Prompt Context

Add prompt construction logic to:

```text
bookworm/prompts.py
```

Good examples:

* load project-specific instructions
* load summaries
* load `.bookworm` memory
* add repo metadata
* add selected source documents

Avoid adding large prompt blocks directly into `agent.py`.

---
