# CLI APIs

## Console Command

Defined in:

```text
pyproject.toml
```

Current entry:

```toml
[project.scripts]
bookworm = "bookworm.cli:main"
```

## Purpose

This allows the user to run:

```powershell
bookworm
```

## Setup Requirement

The console command works after installing the package in editable mode:

```powershell
pip install -e .
```

Use this during development so changes to source files are immediately reflected.

---

## Module Entry Point

Defined in:

```text
bookworm/__main__.py
```

Main command:

```powershell
python -m bookworm
```

## Purpose

This is a fallback entry point that does not rely on the console script being installed.

Expected file:

```python
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

Both entry points should go through the same startup path:

```text
bookworm.cli:main
```

---
