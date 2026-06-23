# GUI Naming Migration Plan

> **Status:** Declaration only — no renames applied yet.  
> **Vocabulary:** chat (entity) · Side Panel (left list) · Main Panel (right conversation view)

This document lists every file, path, symbol, and string change required to align the codebase with [design.md](design.md) and [feature-list.md](feature-list.md).

---

## 1. File renames

### 1.1 Models

| Current | New |
|---|---|
| `bookworm/gui/models/thread.py` | `bookworm/gui/models/chat.py` |
| `bookworm/gui/models/thread_store.py` | `bookworm/gui/models/chat_store.py` |

### 1.2 Controllers

| Current | New |
|---|---|
| `bookworm/gui/controllers/thread_controller.py` | `bookworm/gui/controllers/side_panel_controller.py` |
| `bookworm/gui/controllers/chat_controller.py` | `bookworm/gui/controllers/main_panel_controller.py` |

### 1.3 Views — Side Panel (was thread panel)

| Current | New |
|---|---|
| `bookworm/gui/views/panel/thread_panel.ui` | `bookworm/gui/views/panel/side_panel.ui` |
| `bookworm/gui/views/panel/ui_thread_panel.py` | `bookworm/gui/views/panel/ui_side_panel.py` |
| `bookworm/gui/views/widget/thread_item.ui` | `bookworm/gui/views/widget/chat_item.ui` |
| `bookworm/gui/views/widget/ui_thread_item.py` | `bookworm/gui/views/widget/ui_chat_item.py` |

Regenerate after `.ui` renames:

```bash
pyside6-uic bookworm/gui/views/panel/side_panel.ui -o bookworm/gui/views/panel/ui_side_panel.py
pyside6-uic bookworm/gui/views/widget/chat_item.ui -o bookworm/gui/views/widget/ui_chat_item.py
```

### 1.4 Views — Main Panel (was chat panel)

| Current | New |
|---|---|
| `bookworm/gui/views/panel/chat_panel.ui` | `bookworm/gui/views/panel/main_panel.ui` |
| `bookworm/gui/views/panel/ui_chat_panel.py` | `bookworm/gui/views/panel/ui_main_panel.py` |

Regenerate after `.ui` rename:

```bash
pyside6-uic bookworm/gui/views/panel/main_panel.ui -o bookworm/gui/views/panel/ui_main_panel.py
```

### 1.5 Tests

| Current | New |
|---|---|
| `tests/test_thread_store.py` | `tests/test_chat_store.py` |

### 1.6 Unchanged view files

These stay as-is (names already correct or unrelated):

- `bookworm/gui/views/window/main_window.ui`
- `bookworm/gui/views/window/ui_main_window.py`
- `bookworm/gui/views/widget/message_bubble.ui`
- `bookworm/gui/views/widget/ui_message_bubble.py`

---

## 2. On-disk JSON paths

### 2.1 Directory

| Current | New |
|---|---|
| `<working_dir>/.bookworm/threads/` | `<working_dir>/.bookworm/chats/` |

Hard-coded today in [app_controller.py](controllers/app_controller.py):

```python
threads_dir = config.working_dir / ".bookworm" / "threads"
```

Becomes:

```python
chats_dir = config.working_dir / ".bookworm" / "chats"
```

### 2.2 Per-chat JSON files

| Current | New |
|---|---|
| `.bookworm/threads/<uuid>.json` | `.bookworm/chats/<uuid>.json` |

- Filename pattern stays `{id}.json` — only the parent directory changes.
- JSON **keys are unchanged** in this migration: `id`, `name`, `created_at`, `updated_at`, `messages` (and future `user-input`).

### 2.3 Repo-local sample data

| Current | Action |
|---|---|
| `.bookworm/threads/d6d096c1-9c71-4cd7-aba2-93150bf1a1cb.json` | Move to `.bookworm/chats/` or delete (dev artifact; should not ship in repo) |

---

## 3. Python symbols

### 3.1 Classes

| Current | New | Defined in |
|---|---|---|
| `Thread` | `Chat` | `models/chat.py` |
| `ThreadStore` | `ChatStore` | `models/chat_store.py` |
| `ThreadController` | `SidePanelController` | `controllers/side_panel_controller.py` |
| `ChatController` | `MainPanelController` | `controllers/main_panel_controller.py` |
| `Ui_ThreadPanel` | `Ui_SidePanel` | `views/panel/ui_side_panel.py` |
| `Ui_ThreadItem` | `Ui_ChatItem` | `views/widget/ui_chat_item.py` |
| `Ui_ChatPanel` | `Ui_MainPanel` | `views/panel/ui_main_panel.py` |

### 3.2 Functions

| Current | New | Defined in |
|---|---|---|
| `default_thread_name()` | `default_chat_name()` | `models/chat.py` |
| `validate_thread_data()` | `validate_chat_data()` | `models/chat.py` |

`validate_message_data()` — **unchanged** (messages are not renamed).

### 3.3 `Chat` constructor parameter

| Current | New |
|---|---|
| `Thread(thread_id=...)` | `Chat(chat_id=...)` |

Internal attribute stays `self.id`.

### 3.4 `ChatStore` attributes / methods

| Current | New |
|---|---|
| `threads_dir` | `chats_dir` |
| `self.threads` | `self.chats` |
| `_path_for(thread_id)` | `_path_for(chat_id)` |
| Methods taking `thread: Thread` | `chat: Chat` |
| `get(thread_id)` | `get(chat_id)` |

### 3.5 Qt signals (`SidePanelController`)

| Current | New |
|---|---|
| `thread_selected` | `chat_selected` |
| `thread_created` | `chat_created` |
| `thread_renamed` | `chat_renamed` |
| `thread_deleted` | `chat_deleted` |

`theme_toggle_requested` — **unchanged**.

### 3.6 `AppController` renames (representative)

| Current | New |
|---|---|
| `self.store: ThreadStore` | `self.store: ChatStore` |
| `self.current_thread_id` | `self.current_chat_id` |
| `self.thread_controller` | `self.side_panel_controller` |
| `self.chat_controller` | `self.main_panel_controller` |
| `_create_default_thread()` | `_create_default_chat()` |
| `_save_current_thread()` | `_save_current_chat()` |
| `_select_thread()` | `_select_chat()` |
| `update_thread_panel()` | `update_side_panel()` |
| `on_thread_selected()` | `on_chat_selected()` |
| `on_thread_created()` | `on_chat_created()` |
| `on_thread_renamed()` | `on_chat_renamed()` |
| `on_thread_deleted()` | `on_chat_deleted()` |

### 3.7 `SidePanelController` renames (representative)

| Current | New |
|---|---|
| `self.threads` | `self.chats` |
| `self.filtered_threads` | `self.filtered_chats` |
| `self.active_thread_id` | `self.active_chat_id` |
| `self.thread_list` | `self.chat_list` |
| `self.new_thread_btn` | `self.new_chat_btn` |
| `update_thread_list()` | `update_chat_list()` |
| `update_thread_display()` | `update_chat_display()` |
| `group_threads_by_date()` | `group_chats_by_date()` |
| `_create_thread_item_widget()` | `_create_chat_item_widget()` |
| `set_active_thread_id()` | `set_active_chat_id()` |
| `on_new_thread_clicked()` | `on_new_chat_clicked()` |
| `on_thread_clicked()` | `on_chat_clicked()` |
| `rename_thread()` | `rename_chat()` |
| `delete_thread()` | `delete_chat()` |

### 3.8 Package exports

Update [models/__init__.py](models/__init__.py), [controllers/__init__.py](controllers/__init__.py), and [__init__.py](__init__.py) to export the new names.

---

## 4. `GUIConfig` keys ([config.py](config.py))

| Current | New |
|---|---|
| `thread_panel_width` | `side_panel_width` |
| `thread_panel_min_width` | `side_panel_min_width` |
| `chat_panel_min_height` | `main_panel_min_height` |
| `max_threads` | `max_chats` |

---

## 5. Qt Designer — class names, object names, UI strings

Edit in `.ui` files, then regenerate `ui_*.py`.

### 5.1 `side_panel.ui` (was `thread_panel.ui`)

| Kind | Current | New |
|---|---|---|
| `<class>` | `ThreadPanel` | `SidePanel` |
| Root widget `name` | `ThreadPanel` | `SidePanel` |
| `QListWidget` `name` | `threadList` | `chatList` |
| `QPushButton` `name` | `newThreadButton` | `newChatButton` |
| Placeholder | `Search threads...` | `Search chats...` |
| Tooltip | `Sort threads` | `Sort chats` |
| Tooltip | `New Thread` | `New Chat` |

### 5.2 `chat_item.ui` (was `thread_item.ui`)

| Kind | Current | New |
|---|---|---|
| `<class>` | `ThreadItem` | `ChatItem` |
| Root `QFrame` `name` | `threadItemFrame` | `chatItemFrame` |
| Placeholder label | `Thread name` | `Chat name` |

CSS selector in controller: `QFrame#threadItemFrame` → `QFrame#chatItemFrame`.

### 5.3 `main_panel.ui` (was `chat_panel.ui`)

| Kind | Current | New |
|---|---|---|
| `<class>` | `ChatPanel` | `MainPanel` |
| Root widget `name` | `ChatPanel` | `MainPanel` |

Widget object names inside (`scrollArea`, `messageInput`, `sendButton`, etc.) — **unchanged**.

### 5.4 Dialog strings (in `side_panel_controller.py`)

| Current | New |
|---|---|
| `"Rename Thread"` | `"Rename Chat"` |
| `"Enter new thread name:"` | `"Enter new chat name:"` |
| `"Delete Thread"` / `"Are you sure..."` | `"Delete Chat"` / updated wording |

---

## 6. Default display strings (code + JSON content)

| Current | New |
|---|---|
| `"New Thread {time} {date}"` | `"New Chat {time} {date}"` |
| Welcome message: `"...delete threads..."` | `"...delete chats..."` |

---

## 7. Files that reference old names (update imports only)

These files are **not renamed** but must be edited after the migration:

| File | What to update |
|---|---|
| [controllers/app_controller.py](controllers/app_controller.py) | Imports, controllers, store path, all handlers |
| [controllers/__init__.py](controllers/__init__.py) | Exports |
| [models/__init__.py](models/__init__.py) | Exports |
| [models/message.py](models/message.py) | Module docstring (“conversation thread” → “chat”) |
| [__init__.py](__init__.py) | Module docstring and public API |
| [design.md](design.md) | Path examples (`.bookworm/threads/` → `.bookworm/chats/`) |
| [feature-list.md](feature-list.md) | File tree, code references, `pyside6-uic` examples |
| [tests/test_chat_store.py](tests/test_chat_store.py) | Imports, test names, temp dir `threads/` → `chats/` |
| `.cursor/plans/gui_remaining_features_73744521.plan.md` | Optional; stale path references |

---

## 8. Suggested execution order

1. Rename model files + symbols (`Chat`, `ChatStore`, path constant).
2. Add `.bookworm/threads/` → `.bookworm/chats/` migration in `ChatStore.load()`.
3. Rename and regenerate Side Panel `.ui` / `ui_*.py`; rename `side_panel_controller.py`.
4. Rename and regenerate Main Panel `.ui` / `ui_*.py`; rename `main_panel_controller.py`.
5. Update `app_controller.py`, `config.py`, package `__init__` files.
6. Rename and fix tests.
7. Update `design.md`, `feature-list.md`, and this file’s status to **DONE**.
8. Run `pytest tests/test_chat_store.py tests/test_gui.py`.

---

## 9. Out of scope for this migration

- Renaming the `Message` model or message JSON shape.
- Renaming `AppController` or `main_window.ui`.
- CLI subcommands (`bookworm gui`, `bookworm terminal`).
- Backend agent / LLM code outside `bookworm/gui/`.
- Adding the planned `user-input` JSON field (separate feature).

---

## 10. Checklist (tick when done)

- [ ] Model files renamed
- [ ] Controller files renamed
- [ ] View `.ui` files renamed and `ui_*.py` regenerated
- [ ] Test file renamed
- [ ] `.bookworm/chats/` path wired + legacy migration
- [ ] All imports and symbols updated
- [ ] UI strings updated
- [ ] Docs updated
- [ ] `pytest` passes
