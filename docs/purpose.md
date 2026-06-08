# BookWorm Engineer API Map and Expansion Guide

## Purpose

This document explains the APIs used inside the BookWorm Engineer project and how teammates should extend them safely.

The project follows one main architecture rule:

> Imports should be boring, execution should be explicit.

That means importing a module should not start the app, load `.env`, create clients, read runtime environment variables, or begin the agent loop.

Runtime startup should happen only through:

```powershell
bookworm
```

or:

```powershell
python -m bookworm
```

---
