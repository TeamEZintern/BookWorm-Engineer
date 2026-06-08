# External APIs

## OpenAI SDK

Used in:

```text
bookworm/llm.py
bookworm/agent.py
```

Main calls:

```python
OpenAI(api_key=..., base_url=...)
client.chat.completions.create(...)
```

## Purpose

The OpenAI SDK is used to:

* create an OpenAI-compatible client
* call OpenRouter or OpenAI chat completions
* pass tool schemas to the model
* receive assistant messages
* receive tool calls from the model

## Current Usage

Client creation should happen in:

```text
bookworm/llm.py
```

Example:

```python
from openai import OpenAI

from .config import Config


def create_client(config: Config) -> OpenAI:
    return OpenAI(
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        default_headers={
            "X-OpenRouter-Title": "BookWorm Engineer",
        },
    )
```

Model calls should happen inside:

```text
bookworm/agent.py
```

Example shape:

```python
response = self.client.chat.completions.create(
    model=self.config.llm_model,
    messages=self.messages,
    tools=self.tool_registry.schema,
)
```

## Scaling Guidance

Keep provider-specific setup in `llm.py`.

Good things to add to `llm.py` later:

* provider switching
* OpenRouter-specific headers
* default model options
* retry policy
* request timeout settings
* logging hooks
* fallback providers
* mock clients for tests

Avoid adding provider setup directly to `agent.py`.

---

## `python-dotenv`

Used in:

```text
bookworm/cli.py
```

Main call:

```python
load_dotenv(repo_root / ".env")
```

## Purpose

`python-dotenv` loads local environment variables before config validation.

The `.env` file is useful for local development because teammates can define values like:

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
CONTEXT_WINDOW=128000
GIT_USER_NAME=Your Name
GIT_USER_EMAIL=you@example.com
```

## Scaling Guidance

Keep `.env` loading only in `cli.py`.

Do not load `.env` from:

```text
__init__.py
agent.py
config.py
llm.py
tools/
```

This keeps imports safe and predictable.

---

## `subprocess`

Used in:

```text
bookworm/tools/implementation.py
```

Main call:

```python
subprocess.run(...)
```

## Purpose

`subprocess` allows the agent to run allowlisted terminal commands through the `bash` tool.

This is one of the highest-risk parts of the project because it gives the agent access to the local shell.

## Scaling Guidance

Keep all shell behavior centralized in `implementation.py` for now.

Important safety controls should stay together:

* command allowlisting
* command denylisting
* timeout
* working directory locking
* minimal environment handling
* stdout/stderr capture
* clear error reporting

Eventually, when the file grows, split shell logic into:

```text
bookworm/tools/shell.py
```

Do not scatter shell execution across the codebase.

---
