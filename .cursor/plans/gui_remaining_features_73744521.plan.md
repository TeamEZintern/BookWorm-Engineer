---
name: GUI Remaining Features
overview: "All unchecked items in [bookworm/gui/feature-list.md](bookworm/gui/feature-list.md) — the forward-looking GUI backlog after your cleanup edit. Ten bullet-level gaps across 4 areas: session mode switching, side panel polish, agent message rendering, and draft-input persistence."
todos:
  - id: mode-switch
    content: Mid-session GUI ↔ terminal switching (feature-list line 14)
    status: pending
  - id: overflow-menu-button
    content: Overflow menu button (three dots) on chat_item with rename/delete menu (line 37)
    status: completed
  - id: search-filter
    content: Verify or complete search filtering logic (line 44)
    status: pending
  - id: markdown-parse
    content: Full markdown parsing from raw LLM output (line 78)
    status: completed
  - id: markdown-advanced
    content: Advanced format rendering — code, inline, links, tables (line 79)
    status: completed
  - id: collapsible-sections
    content: Collapsible tool execution / reasoning sections (line 80)
    status: pending
  - id: draft-input-schema
    content: Add draft field to chat JSON schema and Chat model (lines 97, 102–105)
    status: completed
  - id: draft-input-switch
    content: Save/load draft text when switching chats; default empty string (lines 103–105)
    status: completed
isProject: false
---

# GUI Forward Focus — Unchecked Features

After your edit, every `- [ ]` line in [bookworm/gui/feature-list.md](bookworm/gui/feature-list.md) is listed below, grouped by section. These are the features to prioritize next.

---

## 1. Mode Switching

**Switch between GUI and terminal mid-session** (line 14)

- Today: mode is chosen once at launch via CLI (`bookworm` vs `bookworm gui` / `bookworm terminal` in [bookworm/cli.py](bookworm/cli.py)).
- Goal: allow switching modes without restarting the app — e.g. a menu action or command that hands off the session from GUI to terminal (or vice versa) while preserving context.

> Note: line 7 still says GUI is the default; you recently changed CLI default to terminal on another branch. Worth aligning the doc when you next edit it.

---

## 2. Side Panel

### Chat Operations

**Overflow menu button (three dots) → context menu (rename / delete)** (line 37)

- Goal: each chat row gets a visible overflow menu button (three dots) that opens rename/delete, matching the mockup UX.
- Current state: [side_panel_controller.py](bookworm/gui/controllers/side_panel_controller.py) shows rename/delete from the overflow menu button on `chat_item.ui`.

### Search

**Filtering logic** (line 44)

- Goal: real-time chat list filtering as the user types in the search box.
- Current state: **likely already implemented** in [side_panel_controller.py](bookworm/gui/controllers/side_panel_controller.py) (`search_filter`, debounced `apply_search_filter`, name substring match in `apply_sorting_and_filtering`). If it works in the running app, this checkbox may be stale and can be ticked; if not, debug why the wired logic doesn’t surface in the UI.

---

## 3. Main Conversation Panel — Agent Message

Three related rendering gaps under **Agent Message `DOING`**:

### **Markdown parsing from raw LLM output** (line 78) — DONE

- Implemented in [markdown_renderer.py](bookworm/gui/markdown_renderer.py) via the `markdown` library + themed HTML in `QTextBrowser`.
- [main_panel_controller.py](bookworm/gui/controllers/main_panel_controller.py) uses the renderer for all assistant messages.

### **Advanced format render** (line 79) — DONE

- Syntax-highlighted fenced code (Pygments), inline formatting, links, tables, blockquotes, and lists.
- Streaming turns debounce markdown re-renders (~75 ms) and finalize on `turn_complete`.

### **Collapsible sections for tool execution and thinking/reasoning** (line 81) — NEXT

- Goal: when the agent runs tools or emits reasoning/thinking blocks, show them in expandable/collapsible UI sections (similar to ChatGPT tool calls or chain-of-thought disclosure).
- Prerequisite done: real agent integration with structured events (`tool_call_started`, `tool_result`, `reasoning_delta`) via [agent_events.py](bookworm/agent_events.py) and [agent_runner.py](bookworm/gui/agent_runner.py); metadata is stored on `Message.tool_calls`. Collapsible widgets are UI-only from here.

---

## 4. Data Management — Chat Storage

Parent item **Structured JSON schema** (line 97) is now checked because `draft` persistence is implemented:

### **`draft` field** (lines 102–105)

Each chat JSON file under `.bookworm/chats/` now includes a draft input field:

| Sub-item | Behavior |
|---|---|
| Store draft text (line 103) | Text in the chat input field is saved as part of the chat’s persisted state |
| Restore on chat switch (line 104) | Switching chats saves the current draft to the previous chat’s JSON and loads the next chat’s draft into the input field |
| Empty default (line 105) | Use `""` when no draft exists yet |

- Current state: [chat.py](bookworm/gui/models/chat.py) serializes `draft`, defaults missing values to `""`, and the GUI saves/restores draft text when switching chats.

---

## Summary map

```mermaid
flowchart TB
  subgraph mode [Mode Switching]
    M1[midSession GUItoTerminal]
  end
  subgraph chats [Side Panel]
    T1["Overflow menu button (three dots)"]
    T2[Search filter verify or fix]
  end
  subgraph chat [Agent Messages]
    C1[Full markdown parsing]
    C2[Advanced render]
    C3[Collapsible tool or reasoning blocks]
  end
  subgraph data [Chat JSON]
    D1[draft field]
    D2[Save restore on switch]
  end
  C1 --> C2
  C2 --> C3
  D1 --> D2
```

**Count:** 4 top-level unchecked bullets + 3 nested `draft` bullets = **7 distinct feature areas** (search may be verify-and-tick only).

---

## Suggested priority (optional)

If you want an order that unblocks the most user-visible value:

1. **Draft persistence** — small schema + controller change; improves daily UX immediately
2. **Overflow menu button (three dots)** — UI-only; reuses existing rename/delete handlers
3. ~~**Real markdown + advanced render**~~ — done ([markdown_render_upgrade plan](markdown_render_upgrade_f7bbcb4c.plan.md))
4. **Collapsible tool/reasoning sections** — event protocol ready; UI widgets remain
5. **Mid-session mode switch** — architectural; lowest urgency unless explicitly required

No code changes in this step — this is the backlog read from your edited feature list.
