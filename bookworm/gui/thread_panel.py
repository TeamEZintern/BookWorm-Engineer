"""
Thread Panel Component

This module implements the left panel that displays conversation threads.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QLineEdit, QPushButton, QLabel,
    QMenu, QFrame, QToolTip
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QTimer, QEvent
from PySide6.QtGui import QFont, QColor, QCursor

from ..config import Config
from .config import GUIConfig
class Thread:
    """Represents a conversation thread."""
    
    def __init__(self, thread_id: str, name: str, created_at: datetime, 
                 updated_at: datetime, messages: List[Dict[str, Any]] = None):
        self.id = thread_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at
        self.messages = messages or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert thread to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Thread':
        """Create thread from dictionary."""
        return cls(
            thread_id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=data.get("messages", [])
        )
class ThreadPanel(QWidget):
    """
    Left panel displaying conversation threads.
    
    Features:
    - Create, rename, delete, and switch threads
    - Search functionality
    - Sorting by name, date created, or date modified
    - Date grouping for chronological view
    """
    
    def __init__(self, config: GUIConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.threads: List[Thread] = []
        self.filtered_threads: List[Thread] = []
        self.current_sort = "date_modified"  # date_created, date_modified, name
        self.search_filter = ""
        
        self.setup_ui()
        self.update_thread_list()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with search and controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 5)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search threads...")
        self.search_input.textChanged.connect(self.on_search_changed)
        header_layout.addWidget(self.search_input, 1)
        
        # Sort dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Date Modified", "Date Created", "Name"])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        header_layout.addWidget(self.sort_combo, 0)
        
        # New thread button
        self.new_thread_btn = QPushButton("+ New Thread")
        self.new_thread_btn.clicked.connect(self.on_new_thread_clicked)
        header_layout.addWidget(self.new_thread_btn, 0)
        
        layout.addLayout(header_layout)
        
        # Thread list
        self.thread_list = QListWidget()
        self.thread_list.itemClicked.connect(self.on_thread_clicked)
        self.thread_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thread_list.customContextMenuRequested.connect(self.on_context_menu_requested)
        
        layout.addWidget(self.thread_list, 1)
        
        # Set up proxy model for filtering and sorting
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.thread_list.model())
        self.thread_list.setModel(self.proxy_model)
        
        # Set up timer for search debouncing
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_search_filter)
    
    def update_thread_list(self, threads: List[Thread] = None):
        """Update the thread list with new threads."""
        if threads is not None:
            self.threads = threads
        
        self.apply_sorting_and_filtering()
    
    def apply_sorting_and_filtering(self):
        """Apply sorting and filtering to the thread list."""
        # Filter by search text
        filtered = self.threads
        if self.search_filter:
            filtered = [t for t in filtered 
                       if self.search_filter.lower() in t.name.lower()]
        
        # Sort based on current sort option
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
        
        # Group threads by date for better organization
        grouped_threads = self.group_threads_by_date(self.filtered_threads)
        
        for date, threads in grouped_threads.items():
            # Add date header
            date_item = QListWidgetItem(f"  {date}")
            date_item.setFlags(Qt.NoItemFlags)
            date_item.setTextAlignment(Qt.AlignLeft)
            font = date_item.font()
            font.setBold(True)
            date_item.setFont(font)
            self.thread_list.addItem(date_item)
            
            # Add thread items
            for thread in threads:
                item = QListWidgetItem(f"  {thread.name}")
                item.setData(Qt.UserRole, thread)
                item.setToolTip(f"Created: {thread.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                              f"Modified: {thread.updated_at.strftime('%Y-%m-%d %H:%M')}")
                self.thread_list.addItem(item)
    
    def group_threads_by_date(self, threads: List[Thread]) -> Dict[str, List[Thread]]:
        """Group threads by date for display."""
        groups = {}
        
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
        
        # Sort groups chronologically
        sorted_groups = {}
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
        if item.flags() & Qt.ItemIsEnabled:
            thread = item.data(Qt.UserRole)
            if thread:
                self.on_thread_selected.emit(thread)
    
    def on_context_menu_requested(self, position):
        """Show context menu for thread operations."""
        item = self.thread_list.itemAt(position)
        if item and item.flags() & Qt.ItemIsEnabled:
            thread = item.data(Qt.UserRole)
            if thread:
                self.show_context_menu(position, thread)
    
    def show_context_menu(self, position, thread: Thread):
        """Show context menu for thread operations."""
        menu = QMenu(self)
        
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.rename_thread(thread))
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_thread(thread))
        
        menu.popup(self.thread_list.mapToGlobal(position))
    
    def rename_thread(self, thread: Thread):
        """Rename a thread."""
        from PySide6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Thread", "Enter new thread name:", text=thread.name
        )
        
        if ok and new_name:
            thread.name = new_name
            thread.updated_at = datetime.now()
            self.apply_sorting_and_filtering()
    
    def delete_thread(self, thread: Thread):
        """Delete a thread."""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, "Delete Thread",
            f"Are you sure you want to delete the thread '{thread.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.threads.remove(thread)
            self.apply_sorting_and_filtering()
    
    # Signal definitions
    from PySide6.QtCore import pyqtSignal
    on_thread_selected = pyqtSignal(object)