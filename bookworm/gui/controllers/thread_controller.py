"""
Thread Controller

Owns the thread panel view (``ui_thread_panel``) and the thread item widget
(``ui_thread_item``). Handles searching, sorting, date grouping, and thread
create/rename/delete/select operations. Wires widget signals via ``findChild()``
and emits ``thread_selected`` when the user picks a thread.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QComboBox, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMenu, QInputDialog, QMessageBox,
)

from ..models import Thread
from ..views.panel.ui_thread_panel import Ui_ThreadPanel
from ..views.widget.ui_thread_item import Ui_ThreadItem


class ThreadController(QObject):
    """
    Controller for the conversation threads panel.

    Features:
    - Create, rename, delete, and switch threads
    - Search functionality
    - Sorting by name, date created, or date modified
    - Date grouping for chronological view
    """

    thread_selected = Signal(object)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.threads: List[Thread] = []
        self.filtered_threads: List[Thread] = []
        self.current_sort = "date_modified"  # date_created, date_modified, name
        self.search_filter = ""

        self.widget = QWidget()
        self.ui = Ui_ThreadPanel()
        self.ui.setupUi(self.widget)

        self.search_input = self.widget.findChild(QLineEdit, "searchInput")
        self.sort_combo = self.widget.findChild(QComboBox, "sortCombo")
        self.new_thread_btn = self.widget.findChild(QPushButton, "newThreadButton")
        self.thread_list = self.widget.findChild(QListWidget, "threadList")

        self.search_input.textChanged.connect(self.on_search_changed)
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        self.new_thread_btn.clicked.connect(self.on_new_thread_clicked)
        self.thread_list.itemClicked.connect(self.on_thread_clicked)
        self.thread_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self.on_context_menu_requested)

        # Timer for search debouncing
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_search_filter)

        self.update_thread_list()

    def update_thread_list(self, threads: Optional[List[Thread]] = None):
        """Update the thread list with new threads."""
        if threads is not None:
            self.threads = threads
        self.apply_sorting_and_filtering()

    def apply_sorting_and_filtering(self):
        """Apply sorting and filtering to the thread list."""
        filtered = self.threads
        if self.search_filter:
            filtered = [t for t in filtered
                        if self.search_filter.lower() in t.name.lower()]

        if self.current_sort == "date_created":
            filtered.sort(key=lambda t: t.created_at, reverse=True)
        elif self.current_sort == "date_modified":
            filtered.sort(key=lambda t: t.updated_at, reverse=True)
        else:  # name
            filtered.sort(key=lambda t: t.name.lower())

        self.filtered_threads = filtered
        self.update_thread_display()

    def update_thread_display(self):
        """Update the thread list widget with filtered threads."""
        self.thread_list.clear()

        grouped_threads = self.group_threads_by_date(self.filtered_threads)

        for date, threads in grouped_threads.items():
            date_item = QListWidgetItem(f"  {date}")
            date_item.setFlags(Qt.ItemFlag.NoItemFlags)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            font = date_item.font()
            font.setBold(True)
            date_item.setFont(font)
            self.thread_list.addItem(date_item)

            for thread in threads:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, thread)
                item.setToolTip(
                    f"Created: {thread.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Modified: {thread.updated_at.strftime('%Y-%m-%d %H:%M')}"
                )
                item_widget = self._create_thread_item_widget(thread)
                item.setSizeHint(item_widget.sizeHint())
                self.thread_list.addItem(item)
                self.thread_list.setItemWidget(item, item_widget)

    def _create_thread_item_widget(self, thread: Thread) -> QWidget:
        """Build a thread item widget from ui_thread_item for the list row."""
        widget = QWidget()
        item_ui = Ui_ThreadItem()
        item_ui.setupUi(widget)
        # Let clicks fall through to the list so itemClicked still fires.
        widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        name_label = widget.findChild(QLabel, "nameLabel")
        name_label.setText(thread.name)
        return widget

    def group_threads_by_date(self, threads: List[Thread]) -> Dict[str, List[Thread]]:
        """Group threads by date for display."""
        groups: Dict[str, List[Thread]] = {}

        for thread in threads:
            now = datetime.now()
            delta = now - thread.updated_at

            if delta < timedelta(days=1):
                date_key = "Today"
            elif delta < timedelta(days=2):
                date_key = "Yesterday"
            elif delta < timedelta(days=7):
                date_key = thread.updated_at.strftime("%A")
            elif delta < timedelta(days=30):
                date_key = thread.updated_at.strftime("%B %d")
            else:
                date_key = "Older"

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(thread)

        sorted_groups: Dict[str, List[Thread]] = {}
        for date_key in sorted(groups.keys(), key=lambda x: (
            99 if x == "Older" else
            0 if x == "Today" else
            1 if x == "Yesterday" else
            2
        )):
            sorted_groups[date_key] = groups[date_key]

        return sorted_groups

    def on_search_changed(self, text: str):
        """Handle search input changes."""
        self.search_filter = text
        self.search_timer.start(self.config.search_delay)

    def apply_search_filter(self):
        """Apply the search filter."""
        self.apply_sorting_and_filtering()

    def on_sort_changed(self, index: int):
        """Handle sort option changes."""
        sort_options = ["date_modified", "date_created", "name"]
        if 0 <= index < len(sort_options):
            self.current_sort = sort_options[index]
            self.apply_sorting_and_filtering()

    def on_new_thread_clicked(self):
        """Handle new thread button click."""
        import uuid
        new_thread = Thread(
            thread_id=str(uuid.uuid4()),
            name="New Thread",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[]
        )
        self.threads.append(new_thread)
        self.apply_sorting_and_filtering()
        self.on_thread_clicked(self.thread_list.item(self.thread_list.count() - 1))

    def on_thread_clicked(self, item: QListWidgetItem):
        """Handle thread selection."""
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            thread = item.data(Qt.ItemDataRole.UserRole)
            if thread:
                self.thread_selected.emit(thread)

    def on_context_menu_requested(self, position):
        """Show context menu for thread operations."""
        item = self.thread_list.itemAt(position)
        if item and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            thread = item.data(Qt.ItemDataRole.UserRole)
            if thread:
                self.show_context_menu(position, thread)

    def show_context_menu(self, position, thread: Thread):
        """Show context menu for thread operations."""
        menu = QMenu(self.widget)

        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_thread(thread))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_thread(thread))

        menu.popup(self.thread_list.mapToGlobal(position))

    def rename_thread(self, thread: Thread):
        """Rename a thread."""
        new_name, ok = QInputDialog.getText(
            self.widget, "Rename Thread", "Enter new thread name:", text=thread.name
        )

        if ok and new_name:
            thread.name = new_name
            thread.updated_at = datetime.now()
            self.apply_sorting_and_filtering()

    def delete_thread(self, thread: Thread):
        """Delete a thread."""
        reply = QMessageBox.question(
            self.widget, "Delete Thread",
            f"Are you sure you want to delete the thread '{thread.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.threads.remove(thread)
            self.apply_sorting_and_filtering()
