# BookWorm GUI — Design

## Layout

```
+---------------------------------------------------------------------------------------+
|                         |                                                             |
|  Left Panel (Threads)   |                       Main Panel (Chat)                     |
|                         |                                                             |
|  [Search threads...]    |                        [Agent Banner]                       |
|                         |                                                             |
|  + New Thread [Sort ▼]  |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                      User message                     |  │
| ----------------------- |  │                                                       |  │
|  Design GUI             |  └───────────────────────────────────────────────────────┘  |
|  17 Jun 2026            |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                     Agent response                    |  │
|  Fix RAG bug            |  │                     with formatted                    |  │
|  16 Jun 2026            |  │                     markdown output                   |  |
|                         |  └───────────────────────────────────────────────────────┘  |
|  Add tests              |                                                             |
|  15 Jun 2026            |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                     Tool execution                    │  |
|  ...                    |  │                     [output here]                     │  |
|                         |  └───────────────────────────────────────────────────────┘  |
|                         |                                                             |
|                         |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                     Type a message                    │  |
|                         |  └───────────────────────────────────────────────────────┘  |
+---------------------------------------------------------------------------------------+
```

## Panels

### Left Panel — Conversation Threads

Lists all saved conversations. Each thread shows:

- **Thread name** (editable via rename)
- **Date created** or **date last modified** (depending on sort)
- **Context menu** (right-click): Rename, Delete

#### Thread operations

| Action | Behaviour |
|---|---|
| **Create** | Click `+ New Thread`. A new empty thread appears with a default name (e.g. "New Thread"). The name is immediately editable. |
| **Rename** | Double-click the thread name or use right-click → Rename. Inline editing replaces the label. |
| **Delete** | Right-click → Delete. A confirmation dialog appears before removal. |
| **Switch** | Single-click a thread to load its conversation into the main panel. |

#### Sorting

A sort dropdown at the top of the left panel offers three options:

| Sort mode | Behaviour |
|---|---|
| **Date created** | Newest first |
| **Date modified** | Most recently active first (default) |
| **Name** | Alphabetical A→Z |

The current sort mode is persisted per session.

#### Search

A search bar filters threads by name in real time as the user types.

### Main Panel — Conversation

Displays the active thread's message history and the input area.

#### Messages

Messages are rendered as chat bubbles. User messages are aligned right, agent responses left.

- **User messages** — plain text, right-aligned
- **Agent responses** — rendered markdown, left-aligned
- **Tool execution blocks** — collapsible code/output blocks within agent messages
- **Timestamps** — optional, shown on hover or in a compact format for the last message

#### Input area

A multi-line text input at the bottom of the main panel. The input is cleared on send and preserved across thread switches (draft storage).

#### Agent status

A status indicator (e.g. "Idle", "Thinking...", "Running tool: bash") at the top of the main panel or inline in the conversation.

## Data model

Each thread is stored as a JSON file on disk inside `.bookworm/threads/`:

```
.bookworm/
└── threads/
    ├── 20260617-design-gui.json
    ├── 20260616-fix-rag-bug.json
    └── ...
```

### Thread file schema

```json
{
  "id": "20260617-design-gui",
  "name": "Design GUI",
  "created_at": "2026-06-17T10:30:00Z",
  "updated_at": "2026-06-17T11:15:00Z",
  "messages": [
    {
      "role": "user",
      "content": "Design the GUI layout",
      "timestamp": "2026-06-17T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Here is a proposal...",
      "timestamp": "2026-06-17T10:30:05Z",
      "tool_calls": [...]
    }
  ]
}
```

## Implementation notes

- Thread list is loaded on startup. Sorting and filtering operate on the in-memory list (no re-read from disk).
- New threads default name to "New Thread" with a unique slug for the filename.
- Delete moves the thread file to a trash location or marks it deleted; hard delete is a separate action.
- The active thread is visually highlighted in the thread list.
- Unsaved draft text is stored in memory per thread and discarded on app close (no draft persistence).
