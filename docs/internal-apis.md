# Internal APIs

## `Config` and `load_config`

Defined in:

```text
bookworm/config.py
```

Main usage:

```python
config = load_config(working_dir=Path.cwd())
```

## Purpose

`Config` centralizes runtime settings.

It should own:

* `LLM_API_KEY`
* `LLM_BASE_URL`
* `LLM_MODEL`
* `CONTEXT_WINDOW`
* `GIT_USER_NAME`
* `GIT_USER_EMAIL`
* `WORKING_DIR`

The rest of the application should use the `Config` object instead of reading environment variables directly.

## Example Shape

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    context_window: int
    git_user_name: str
    git_user_email: str
    working_dir: Path
```

## Scaling Guidance

When adding a new runtime setting:

1. Add it to `.env.example`.
2. Add it to `Config`.
3. Parse and validate it in `load_config`.
4. Pass `Config` into the module that needs it.
5. Access it through `self.config` or a function argument.

Do not do this inside random modules:

```python
os.environ["NEW_SETTING"]
```

Prefer this:

```python
config.new_setting
```

---

## `create_client`

Defined in:

```text
bookworm/llm.py
```

Main usage:

```python
client = create_client(config)
```

## Purpose

`create_client` builds the OpenAI-compatible client from `Config`.

This keeps model-provider details outside of the agent loop.

## Scaling Guidance

Use `llm.py` as the provider boundary.

Future changes that belong here:

* switching between OpenAI and OpenRouter
* adding Anthropic or other providers through adapters
* default request headers
* timeout configuration
* retry configuration
* client instrumentation
* test doubles or fake clients

---

## `build_system_prompt`

Defined in:

```text
bookworm/prompts.py
```

Main usage:

```python
system_prompt = build_system_prompt(config)
```

## Purpose

`build_system_prompt` creates the system prompt used by the agent.

It may include:

* static system instructions
* `config.working_dir`
* Git identity information
* `AGENTS.md`
* `PROGRESS.md`

## Scaling Guidance

Prompt construction should stay in `prompts.py`.

Do not put large prompt strings back into:

```text
agent.py
cli.py
llm.py
```

If the prompt needs more project context later, add that logic to `prompts.py`.

Good future additions:

* reading `.bookworm/instructions.md`
* reading project summaries
* adding configurable prompt sections
* supporting prompt templates
* supporting different prompt modes

---

## `Agent`

Defined in:

```text
bookworm/agent.py
```

Main usage:

```python
agent = Agent(
    config=config,
    client=create_client(config),
    tool_registry=create_tool_registry(config),
    system_prompt=build_system_prompt(config),
)

agent.run()
```

## Purpose

`Agent` owns the runtime conversation loop.

It should handle:

* storing message history
* accepting user input
* sending messages to the model
* passing tool schemas to the model
* receiving assistant responses
* detecting tool calls
* executing tool calls through the tool registry
* appending tool results back into message history
* tracking context usage
* printing final assistant replies

## Scaling Guidance

`agent.py` should focus on orchestration, not setup.

Do not add these to module-level code in `agent.py`:

```python
os.environ["LLM_API_KEY"]
OpenAI(...)
load_dotenv(...)
create_tool_registry(...)
build_system_prompt(...)
```

Instead, receive dependencies in the constructor:

```python
class Agent:
    def __init__(
        self,
        config: Config,
        client: OpenAI,
        tool_registry: ToolRegistry,
        system_prompt: str,
    ) -> None:
        ...
```

This keeps the agent testable and reusable.

---
