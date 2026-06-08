# Tool APIs

The tools are the capabilities exposed to the model.

Current tools:

```text
read_file
write_file
bash
ask_user
```

The tool system has three parts:

```text
schema.py
  describes tools to the model

implementation.py
  contains the Python functions

registry.py
  binds schema names to callable implementations
```

---

## `ToolRegistry` and `create_tool_registry`

Defined in:

```text
bookworm/tools/registry.py
```

Main usage:

```python
tool_registry = create_tool_registry(config)
```

## Purpose

The tool registry connects tool schemas to actual Python functions.

It allows `agent.py` to stay generic.

Instead of hardcoding tool functions directly in the agent loop, the agent can call:

```python
self.tool_registry.implementations[fn_name](**fn_args)
```

## Expected Shape

```python
@dataclass
class ToolRegistry:
    schema: list[dict]
    implementations: dict[str, Callable[..., str]]
```

Example registration:

```python
return ToolRegistry(
    schema=SCHEMA,
    implementations={
        "read_file": read_file,
        "write_file": write_file,
        "bash": bash,
        "ask_user": ask_user,
    },
)
```

## Scaling Guidance

Every new tool should be added in three places:

1. Add the tool schema in `schema.py`.
2. Add the function implementation in `implementation.py`.
3. Register the schema name to the function in `registry.py`.

The tool name in the schema must match the key in `implementations`.

Example:

```python
# schema.py
{
    "type": "function",
    "function": {
        "name": "read_file",
        ...
    },
}
```

Must match:

```python
# registry.py
"read_file": read_file
```

---

## Tool Schemas

Defined in:

```text
bookworm/tools/schema.py
```

Current export:

```python
SCHEMA
```

## Purpose

Tool schemas tell the model:

* what tools exist
* what each tool does
* what arguments each tool accepts
* which arguments are required

## Example Schema

```python
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file from the working directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file relative to the working directory.",
                }
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    },
}
```

## Scaling Guidance

Keep schemas explicit and boring.

Recommended schema rules:

* Use clear descriptions.
* Use `additionalProperties: False` where possible.
* Keep argument names stable.
* Make required arguments explicit.
* Avoid overly broad tools.
* Avoid tools that can perform many unrelated actions.

Good tool:

```text
read_file
```

Risky tool:

```text
do_anything_on_computer
```

---

## Tool Implementations

Defined in:

```text
bookworm/tools/implementation.py
```

Current callable APIs:

```python
read_file(file_path: str) -> str
write_file(file_path: str, content: str) -> str
bash(command: str) -> str
ask_user(question: str) -> str
```

## Purpose

Tool implementations are the actual local capabilities the model can call.

They should return strings because tool results are passed back into the model conversation.

## Current Tools

### `read_file`

```python
read_file(file_path: str) -> str
```

Reads a file inside the configured working directory.

Expected behavior:

* resolve the path safely
* prevent path traversal outside the working directory
* return file content
* return a clear error string if the file cannot be read

---

### `write_file`

```python
write_file(file_path: str, content: str) -> str
```

Writes content to a file inside the configured working directory.

Expected behavior:

* resolve the path safely
* prevent writing outside the working directory
* create parent folders if needed
* write UTF-8 text
* return a success or error string

---

### `bash`

```python
bash(command: str) -> str
```

Runs an allowlisted shell command inside the configured working directory.

Expected behavior:

* validate command against policy
* block dangerous commands
* run with a timeout
* capture stdout
* capture stderr
* return the exit code

---

### `ask_user`

```python
ask_user(question: str) -> str
```

Asks the user for more information during an agent run.

Expected behavior:

* display the question clearly
* return the user's answer as a string

---

## Scaling Guidance

Keep implementations narrow.

A tool should do one clear thing.

If `implementation.py` becomes too large, split it into:

```text
bookworm/tools/filesystem.py
bookworm/tools/shell.py
bookworm/tools/user.py
```

Suggested future split:

```text
filesystem.py
  read_file
  write_file
  path validation helpers

shell.py
  bash
  allowlist
  denylist
  timeout
  subprocess handling

user.py
  ask_user

registry.py
  imports implementations and registers tools
```

---
