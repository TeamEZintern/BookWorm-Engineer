# BookWorm GUI — Feature List

> In-depth design implementation log for the BookWorm GUI.

## Mode Switching `DONE`

GUI is default mode when running `bookworm`, terminal accessible with `bookworm terminal`

- [x] Command-line argument parsing
- [x] GUI mode detection working
- [x] GUI window launch wired into CLI
- [x] PySide6 added to dependencies
- [x] Choose at the start of a session
- [ ] Switch in between GUI and terminal in the middle of a session

---

## Side Panel `TODO`

Side panel displaying list of saved chats with chat names

### Chat Display `DOING`

Shows chat name, creation/modified date, context menu

- [x] UI components
- [x] Date grouping

### Chat Operations `DOING`

Create, rename, delete, and switch between chats

- [x] Click on chat in side panel to open its coversation in the main panel
- [x] If a chat's converstaion is already opened in the main panel, clicking on it in the side panel does nothing
- [x] Clicking a different chat saves the current conversation and loads the selected one, replacing the main panel content entirely.
- [x] Create/delete functionality
- [ ] Overflow menu button (three dots) on a chat item shows a context menu to rename or delete it

### Search `DOING`

Real-time chat filtering by name

- [x] Search input
- [ ] Filtering logic

### Date Grouping `DONE`

Groups chats by calendar day when sorted by Date created or Date modified

- [x] Grouping by day/week/month
- [x] Visual headers

### Sorting `DONE`

Sort chats by Date created, Date modified, or Name

- [x] Sort dropdown
- [x] Sort functionality

---

## Main Panel `DOING`

Main panel displaying active conversation with message history

### User Messages `DONE`

Chat messages given by user

- [x] User input field
- [x] Message bubble UI
- [x] Timestamp display under message bubble

### Agent Message `DOING`

Agent responses rendered as formatted markdown

- [ ] Markdown parsing from raw LLM output
- [ ] Advanced format render
- [ ] Collapsible sections for tool execution and thinking/reasoning
- [x] Copy and Redo buttons at the bottom.
  - Copy means to copy the raw markdown of the agent output.
  - Redo means re-prompting the agent with the same user input to get a new response, often because the original output had a glitch or the user was not satisfied with it.

---

## Data Management `DONE`

Backend data structures and storage for GUI functionality

### Chat Storage `DONE`

JSON files stored in `.bookworm/chats/` directory, which is initialized in user's repository, not in the BookWorm-Engineer repository.

- [x] File path structure defined (`<chat_id>.json`)
- [x] Persistence layer implemented in `ChatStore`
- [x] Structured JSON schema
  - [x] id
  - [x] name
  - [x] timestamps
  - [x] messages
  - [x] draft
    - [x] Text typed into the message input field is stored as part of a chat's memory
    - [x] When user switches between chats, the drafted message of the previous chat is saved in the JSON, and the drafted message of the next chat is loaded into the message input field.
    - [x] Empty string in the case of there being no text in the message input field yet.

---

## Additional UI/UX enhancements `DOING`

- [x] Context menus
- [x] Theme toggle button (header bar)
- [x] Light and dark colour palettes (`themes.py`)
- [x] Global QSS stylesheet cascades to all standard widgets
- [x] Theme-aware inline styles for message bubbles, inputs, buttons
- [x] Live theme switching without restart


### Visual Feedback `DONE`

Active chat highlighting and visual indicators

- [x] Highlighting implemented
- [x] Selection feedback working

### Confirmation Dialogs `DONE`

User confirmation for destructive actions like deletion

- [x] Delete confirmation implemented
- [x] Error dialogs added

---

## MVC Migration `DONE`

Split monolithic panels into View (`Qt Designer .ui` + `pyside6-uic` generated `.py`), Controller, and Model layers.

### Proposed file structure

```
bookworm/gui/
├── __init__.py
├── config.py
├── themes.py
│
├── views/
│   ├── window/
│   │   ├── main_window.ui
│   │   └── ui_main_window.py
│   ├── panel/
│   │   ├── side_panel.ui
│   │   ├── ui_side_panel.py
│   │   ├── main_panel.ui
│   │   └── ui_main_panel.py
│   └── widget/
│       ├── message_bubble.ui
│       ├── ui_message_bubble.py
│       ├── chat_item.ui
│       └── ui_chat_item.py
│
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py
│   ├── side_panel_controller.py
│   └── main_panel_controller.py
│
└── models/
    ├── __init__.py
    ├── chat.py
    ├── message.py
    └── chat_store.py
```

### Design decisions

- [x] `.ui` and generated `ui_*.py` sit side-by-side in the same subfolder
- [x] `.ui` files conform to the Qt Designer UI file format (`qt-designer-schema.xml`)
- [x] Layout source of truth is the `.ui` files — edit them in Qt Designer (or equivalent), not by hand-editing XML
- [x] Chat row template is `views/widget/chat_item.ui`; `side_panel.ui` only defines the empty `QListWidget` — chat names are runtime data, not static Designer entries
- [x] Do **not** hand-edit `ui_*.py` — they are generated output and will be overwritten on the next build
- [x] Controller uses `findChild()` to wire up widget signals (no view wrapper layer)
- [x] View files (.ui + generated) created
- [x] Controller files created (app, side panel, main panel)
- [x] Model files extracted (chat, message, chat_store)
- [x] Monolithic panels deleted (main_panel.py, side_panel.py, main_window.py reworked)

### `.ui` to `.py` conversion (`pyside6-uic`)

Workflow:

1. Edit the `.ui` file in Qt Designer and save.
2. Run `pyside6-uic <file_dir>/<filename>.ui -o <file_dir>/ui_<file_name>.py` from the repo root. For example: `pyside6-uic bookworm/gui/views/panel/side_panel.ui -o bookworm/gui/views/panel/ui_side_panel.py`
3. Commit both the updated `.ui` and the regenerated `ui_*.py`.

Based on [PySide6 docs](https://doc.qt.io/qtforpython-6/tools/pyside-uic.html):

- `pyside6-uic` is a CLI wrapper around Qt's `uic` tool with Python support
- Convert a `.ui` file: `pyside6-uic your_file.ui -o ui_your_file.py`
- The `-o` flag writes output to a file (without it, output goes to stdout)
- Generates a class `Ui_TheNameOfYourDesign(object)` with a `setupUi(widget)` method
- Usage in code: instantiate the `Ui`_* class and call `setupUi(self)` on a matching Qt widget (e.g. `QWidget`, `QDialog`, `QMainWindow`)
- Do **not** hand-edit `ui_*.py` — changes are lost on re-generation; put layout changes in the `.ui` file instead
- Prefer `pyside6-uic` over raw `uic -g python` to avoid version mismatches
- For a full list of options: `pyside6-uic -h`
