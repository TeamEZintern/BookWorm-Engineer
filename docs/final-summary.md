# Final Summary

The project is organized around explicit startup and boring imports.

The clean flow is:

```text
bookworm command
  -> bookworm.cli:main
  -> load .env
  -> load Config
  -> create LLM client
  -> create ToolRegistry
  -> build system prompt
  -> create Agent
  -> run Agent
```

The most important rule for future work is:

> Add capabilities by passing dependencies through `Config`, `ToolRegistry`, or constructor arguments. Do not add hidden startup behavior during import.

Following this keeps the project easy to test, easy to package, and safe to extend.
