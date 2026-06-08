# Safety Rules for Future Expansion

## 1. Do not start runtime behavior during import

Avoid this:

```python
client = OpenAI(...)
agent = Agent(...)
agent.run()
```

at module level.

Prefer this:

```python
def main() -> int:
    ...
```

---

## 2. Do not read environment variables everywhere

Avoid this:

```python
model = os.environ["LLM_MODEL"]
```

Prefer this:

```python
model = config.llm_model
```

---

## 3. Keep shell execution centralized

Avoid adding `subprocess.run` in random modules.

Keep shell access in:

```text
bookworm/tools/implementation.py
```

or later:

```text
bookworm/tools/shell.py
```

---

## 4. Keep tools explicit

Each tool should have:

```text
schema
implementation
registry entry
```

Avoid tools with vague powers.

---

## 5. Keep `agent.py` focused on orchestration

`agent.py` should coordinate the conversation loop.

It should not own:

* `.env` loading
* config parsing
* prompt construction
* client construction
* raw tool implementation logic

---
