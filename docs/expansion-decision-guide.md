# Expansion Decision Guide

Use this guide when deciding where new code belongs.

## "I need a new environment variable."

Add it to:

```text
config.py
.env.example
```

Use it through:

```python
config.some_value
```

---

## "I need to change the model provider."

Add it to:

```text
llm.py
```

---

## "I need to change the system prompt."

Add it to:

```text
prompts.py
```

---

## "I need to change how the agent loops."

Add it to:

```text
agent.py
```

---

## "I need to add a new tool."

Add it to:

```text
tools/schema.py
tools/implementation.py
tools/registry.py
```

---

## "I need to change how the app starts."

Add it to:

```text
cli.py
__main__.py
pyproject.toml
```

---
