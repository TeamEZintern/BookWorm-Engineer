# BookWorm GUI

## What

A graphical chatbot application (similar to ChatGPT, Claude, Gemini) that wraps the Bookworm AI coding agent in a user-friendly interface.

## Why

The current terminal interface is difficult to read — raw markdown text leaves special characters (`#`, `*`, `` ` ``) visible, and word wrap splits words unpredictably. A GUI renders markdown properly, provides clean message bubbles, and gives visual feedback for agent status, tool execution, and source management.

## How

- **PySide6** — chosen for licensing flexibility (LGPL) and native Python integration
- **Architecture** — separate `gui/` package communicates with the existing `bookworm` agent backend; no changes to core agent logic
- **Testing** — pytest for component and integration tests
