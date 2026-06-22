# BookWorm GUI — Feature List

> In-depth design implementation log for the BookWorm GUI.

## GUI Mode Switching `DONE`

GUI is default mode when running `bookworm`, terminal accessible with `bookworm terminal`

- [x] Command-line argument parsing implemented
- [x] GUI mode detection working
- [x] GUI window launch wired into CLI
- [x] PySide6 added to dependencies

### Default GUI Mode `DONE`

Bookworm launches GUI interface by default

- [x] `bookworm` with no args launches GUI
- [x] QApplication + BookwormGUI wired in cli.py

### Mode Switching `TODO`

Ability to switch between GUI and terminal modes

- [x] Choose at the start of a session
- [ ] Switch in between GUI and terminal in the middle of a session

---

## Conversation Threads Panel `TODO`

Left panel displaying list of saved conversations with thread names

- [x] Thread display implemented
- [x] Basic operations working

### Thread Display `DOING`

Shows thread name, creation/modified date, context menu

- [x] UI components created
- [x] Date grouping implemented

### Thread Operations `DOING`

Create, rename, delete, and switch between threads

- [x] Click on thread in thread panel to open its coversation in the chat panel
- [x] If a thread's converstaion is already opened in the chat panel, clicking on it in the thread panel does nothing
- [x] Clicking a different thread saves the current conversation and loads the selected one, replacing the chat panel content entirely.
- [x] Create/delete functionality implemented
- [x] Right clicking a thread shows a context menu to rename or delete it

### Search `TODO`

Real-time thread filtering by name

- [x] Search input added
- [ ] Filtering logic planned

### Date Grouping `DONE`

Groups threads by calendar day when sorted by Date created or Date modified

- [x] Grouping by day/week/month implemented
- [x] Visual headers added

### Sorting `DONE`

Sort threads by Date created, Date modified, or Name

- [x] Sort dropdown implemented
- [x] Sort functionality working

---

## Main Conversation Panel `DOING`

Right panel displaying active conversation with message history

- [x] Basic chat UI created
- [x] Message bubbles implemented

### Message Bubbles `DONE`

Chat-style message display with user and agent alignment

- [x] Message bubble UI created
- [x] Styling applied

### Markdown Rendering `DOING`

Agent responses rendered as formatted markdown

- [x] Basic markdown parsing implemented
- [ ] Advanced formatting planned

### Tool Execution Blocks `TODO`

Collapsible sections for tool execution output

- [x] UI structure prepared
- [ ] Integration pending

### Timestamps `DONE`

Optional message timestamps on hover or compact display

- [x] Timestamp display implemented
- [x] Hover tooltips added

### Input Area `DOING`

Multi-line text input for user messages with send functionality

- [x] Input field created
- [x] Send button functional

### Agent Status `DONE`

Visual indicator showing agent state (Idle, Thinking, Running tool)

- [x] Status bar implemented
- [x] State indicators working

---

## Data Management `DOING`

Backend data structures and storage for GUI functionality

- [x] Thread model created
- [x] Storage abstraction implemented

### Thread Storage `DOING`

JSON files stored in `.bookworm/threads/` directory

- [x] File path structure defined
- [ ] Persistence layer planned

### Thread Schema `DONE`

Structured JSON schema with id, name, timestamps, and messages

- [x] Data model defined
- [x] Schema validation implemented

### Draft Persistence `TODO`

In-memory draft text storage for unsaved messages

- [x] Architecture planned
- [ ] Implementation pending

---

## User Interface Features `DOING`

Additional UI/UX enhancements

- [x] Context menus implemented
- [x] Visual feedback added
- [x] Theme toggle button (header bar)
- [x] Light and dark colour palettes (`themes.py`)
- [x] Global QSS stylesheet cascades to all standard widgets
- [x] Theme-aware inline styles for message bubbles, inputs, buttons
- [x] Live theme switching without restart

### Context Menus `DONE`

Right-click menus for thread operations

- [x] Right-click menus created
- [x] Actions connected

### Inline Editing `DOING`

Double-click thread names for immediate renaming

- [x] Edit mode initiated
- [ ] Validation in progress

### Visual Feedback `DONE`

Active thread highlighting and visual indicators

- [x] Highlighting implemented
- [x] Selection feedback working

### Confirmation Dialogs `DONE`

User confirmation for destructive actions like deletion

- [x] Delete confirmation implemented
- [x] Error dialogs added

---

## Integration Features `TODO`

Integration with Bookworm agent backend

- [x] Architecture defined
- [x] Backend connection planned

### Backend Communication `TODO`

Real-time communication with Bookworm agent

- [x] Connection interface designed
- [ ] Message passing planned

### Thread Synchronization `TODO`

Sync thread state with agent backend

- [x] Sync logic defined
- [ ] Implementation pending

### Message Persistence `TODO`

Persistent storage of conversation history

- [x] Persistence layer designed
- [ ] Auto-save planned

---

## MVC Migration `DONE`

Split monolithic panels into View (`Qt Designer .ui` + `pyside6-uic` generated `.py`), Controller, and Model layers.

### Proposed file structure

```
bookworm/gui/
├── __init__.py
├── build_ui.py              # Finds .ui → runs pyside6-uic
├── config.py
├── themes.py
│
├── views/
│   ├── window/
│   │   ├── main_window.ui
│   │   └── ui_main_window.py
│   ├── panel/
│   │   ├── thread_panel.ui
│   │   ├── ui_thread_panel.py
│   │   ├── chat_panel.ui
│   │   └── ui_chat_panel.py
│   └── widget/
│       ├── message_bubble.ui
│       ├── ui_message_bubble.py
│       ├── thread_item.ui
│       └── ui_thread_item.py
│
├── controllers/
│   ├── __init__.py
│   ├── app_controller.py
│   ├── thread_controller.py
│   └── chat_controller.py
│
└── models/
    ├── __init__.py
    ├── thread.py
    ├── message.py
    └── thread_store.py
```

### Design decisions

- [x] `.ui` and generated `ui_*.py` sit side-by-side in the same subfolder
- [x] Both committed to git
- [x] `.ui` files conform to the Qt Designer UI file format (`qt-designer-schema.xml`)
- [x] Developers run `pyside6-uic` on `.ui` files via `build_ui.py`
- [x] Controller uses `findChild()` to wire up widget signals (no view wrapper layer)
- [x] View files (.ui + generated) created
- [x] Controller files created (app, thread, chat)
- [x] Model files extracted (thread, message, thread_store)
- [x] Monolithic panels deleted (chat_panel.py, thread_panel.py, main_window.py reworked)

### `.ui` to `.py` conversion (`pyside6-uic`)

Regular conversion is handled by `build_ui.py`, which walks the `views/` directory tree, finds all `.ui` files, and runs `pyside6-uic <file>.ui -o ui_<file>.py` in the same folder.

Based on [PySide6 docs](https://doc.qt.io/qtforpython-6/tools/pyside-uic.html):

- `pyside6-uic` is a CLI wrapper around Qt's `uic` tool with Python support
- Convert a `.ui` file: `pyside6-uic your_file.ui -o ui_your_file.py`
- The `-o` flag writes output to a file (without it, output goes to stdout)
- Generates a class `Ui_TheNameOfYourDesign(object)` with a `setupUi(widget)` method
- Usage in code: instantiate the `Ui_*` class and call `setupUi(self)` on a matching Qt widget (e.g. `QWidget`, `QDialog`, `QMainWindow`)
- Do **not** hand-edit generated files — changes are lost on re-generation
- Prefer `pyside6-uic` over raw `uic -g python` to avoid version mismatches
- For a full list of options: `pyside6-uic -h`

