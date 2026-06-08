# Common Mistakes to Avoid

## Mistake 1: Adding env reads inside `agent.py`

Bad:

```python
LLM_MODEL = os.environ["LLM_MODEL"]
```

Good:

```python
self.config.llm_model
```

---

## Mistake 2: Adding new tools only to `implementation.py`

Adding a function is not enough.

A complete tool needs:

```text
schema.py
implementation.py
registry.py
```

---

## Mistake 3: Putting prompt text back into `agent.py`

Bad:

```python
SYSTEM_PROMPT = """very long prompt..."""
```

Good:

```python
system_prompt = build_system_prompt(config)
```

---

## Mistake 4: Creating the client inside `agent.py`

Bad:

```python
client = OpenAI(...)
```

Good:

```python
client=create_client(config)
```

---

## Mistake 5: Forgetting editable install for the CLI command

If this does not work:

```powershell
bookworm
```

Run:

```powershell
pip install -e .
```

Or use:

```powershell
python -m bookworm
```

---
