# BookWorm GUI — Design

## Layout

```
+---------------------------------------------------------------------------------------+
|                         |                                                             |
|      Side Panel         |                       Main Panel                            |
|                         |                                                             |
|  [Search chats...]      |                        [Agent Banner]                       |
|                         |                                                             |
|  + New Chat [Sort ▼]    |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                      User message                     |  │
| ----------------------- |  │                                                       |  │
|  17 Jun 2026            |  └───────────────────────────────────────────────────────┘  |
|  Design GUI             |  ┌───────────────────────────────────────────────────────┐  |
|                         |  │                     Agent response                    |  │
|  16 Jun 2026            |  │                     with formatted                    |  │
|  Fix RAG bug            |  │                     markdown output                   |  |
|  Add tests              |  └───────────────────────────────────────────────────────┘  |
|                         |                                                             |
|  15 Jun 2026            |  ┌───────────────────────────────────────────────────────┐  |
|  Why don't button work  |  │                     Tool execution                    │  |
|  How do I fix colors    |  │                     [output here]                     │  |
|  feet smell             |  └───────────────────────────────────────────────────────┘  |
|  ...                    |                                                             |
|                         |  ┌───────────────────────────────────────────────────────┐  |
|  Older                  |  │                     Type a message                    │  |
|  ...                    |  └───────────────────────────────────────────────────────┘  |
+---------------------------------------------------------------------------------------+
```

## Panels

### Side Panel

Lists all saved chats. Each chat shows:

- **Chat name** (editable via rename)
- **Date created** or **date last modified** (depending on sort)
- **Overflow menu button (three dots)**: Rename, Delete

#### Chat grouping and display

Chats are grouped by calendar day (day-month format) when sorted by **Date created** or **Date modified**:

- **Date created**: chats grouped by creation day (earliest first)
- **Date modified**: chats grouped by modification day (earliest first)

When sorted by **Name**, chats are displayed alphabetically without date grouping.

#### Chat operations

| Action | Behaviour |
|---|---|
| **Create** | Click `+ New Chat`. A new empty chat appears with a default name (e.g. "New Chat"). The name is immediately editable. |
| **Rename** | Double-click the chat name or overflow menu button (three dots) → Rename. Inline editing replaces the label. |
| **Delete** | Overflow menu button (three dots) → Delete. A confirmation dialog appears before removal. |
| **Switch** | Single-click a chat to load its conversation into the main panel. |

#### Sorting

A sort dropdown at the top of the side panel offers three options:

| Sort mode | Behaviour |
|---|---|
| **Date created** | Chats grouped by creation day (earliest first), sorted chronologically |
| **Date modified** | Chats grouped by modification day (earliest first), sorted chronologically |
| **Name** | Alphabetical A→Z |

The current sort mode is persisted per session.

#### Search

A search bar filters chats by name in real time as the user types.

### Main Panel

Displays the active chat's message history and the input area.

#### Messages

Messages are rendered as chat bubbles. User messages are aligned right, agent responses left.

- **User messages** — plain text, right-aligned
- **Agent responses** — rendered markdown via `markdown_renderer.py` (`markdown` + Pygments → themed HTML in a read-only `QTextBrowser`), left-aligned
- **Streaming** — assistant replies stream token-by-token into a placeholder message; markdown re-renders with debouncing during the turn
- **Tool execution blocks** — collapsible code/output blocks within agent messages (planned; tool/reasoning events are already emitted and stored on `Message.tool_calls`)
- **Timestamps** — optional, shown on hover or in a compact format for the last message

#### Input area

A multi-line text input at the bottom of the main panel. The input is cleared on send and preserved across chat switches (draft storage).

#### Agent status

The status bar shows turn progress (e.g. "Thinking...", "Running tool: bash", "Ready"). Agent turns run on a background thread via `AgentRunner`; the UI receives streamed text and structured tool events through Qt signals.

## Data model

Each chat is stored as a JSON file on disk inside `.bookworm/chats/`:

```
.bookworm/
└── chats/
    ├── 20260617-design-gui.json
    ├── 20260616-fix-rag-bug.json
    └── ...
```

### Chat file schema

User messages use a plain string `content`. Assistant messages store one or more **attempts** (each attempt is a full response snapshot: reasoning, tool calls, final answer, etc.). Redo appends a new attempt without deleting prior ones; `active_attempt` records which attempt the UI last displayed.

```json
{
  "id": "20260617-design-gui",
  "name": "Design GUI",
  "created_at": "2026-06-17T10:30:00Z",
  "updated_at": "2026-06-17T10:36:00Z",
  "draft": "",
  "messages": [
    {
      "role": "user",
      "content": "Design the GUI layout",
      "timestamp": "2026-06-17T10:30:00Z"
    },
    {
      "role": "assistant",
      "num_attempts": 2,
      "active_attempt": 2,
      "attempts": [
        {
          "index": 1,
          "content": [
            {
              "type": "final_answer",
              "text": "Use a two-panel layout with a sidebar and main area."
            }
          ],
          "timestamp": "2026-06-17T10:30:05Z"
        },
        {
          "index": 2,
          "content": [
            {
              "type": "reasoning",
              "text": "I should inspect the project structure first."
            },
            {
              "type": "tool_call",
              "id": "call_123",
              "name": "read_file",
              "arguments": "{\"file_path\":\"AGENTS.md\"}"
            },
            {
              "type": "tool_result",
              "tool_call_id": "call_123",
              "content": "# AGENTS.md\n\nProject instructions..."
            },
            {
              "type": "final_answer",
              "text": "Here is a proposal for a side panel plus main panel layout..."
            }
          ],
          "timestamp": "2026-06-17T10:31:22Z"
        }
      ]
    },
    {
      "role": "user",
      "content": "Suppose this prompt causes the agent to produce an error.",
      "timestamp": "2026-06-17T10:35:00Z"
    },
    {
      "role": "assistant",
      "num_attempts": 1,
      "active_attempt": 1,
      "attempts": [
        {
          "index": 1,
          "content": [
            {
              "type": "error_detail",
              "text": "es_config': {'type': <DynamicShapesType.BACKED: 'backed'>}, 'local_cache_dir': None}\n(EngineCore_DP0 pid=25) INFO 12-14 20:43:07 [cpu_worker.py:192] auto thread-binding list (id, physical core): [(2, 0), (3, 1)]\nget_mempolicy: Operation not permitted\n"
            },
            {
              "type": "final_answer",
              "text": "EngineCore encountered an issue. See stack trace (above) for the root cause."
            }
          ],
          "timestamp": "2026-06-17T10:36:00Z"
        }
      ]
    }
  ]
}
```

## Implementation notes

- Chat list is loaded on startup. Sorting and filtering operate on the in-memory list (no re-read from disk).
- New chats default name to "New Chat" with a unique slug for the filename.
- Delete moves the chat file to a trash location or marks it deleted; hard delete is a separate action.
- The active chat is visually highlighted in the side panel.
- Unsaved draft text is stored in each chat JSON file as `draft` and restored when switching chats or reopening the GUI.
