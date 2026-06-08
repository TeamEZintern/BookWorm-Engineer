# High-Level Architecture

The current architecture is:

```text
cli.py
  loads .env, creates config/client/tools/prompt

config.py
  owns environment parsing and validation

llm.py
  owns model provider setup

prompts.py
  owns system prompt construction

agent.py
  owns conversation loop and tool-call orchestration

tools/
  owns safe capabilities exposed to the model
```

The intended dependency direction is:

```text
cli.py
  -> config.py
  -> llm.py
  -> prompts.py
  -> tools/registry.py
  -> agent.py
```

`agent.py` should receive dependencies. It should not create global runtime dependencies during import.

---
