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
