"""
Side Panel Controller

Owns the side panel view (``ui_side_panel``) and the chat item widget
(``ui_chat_item``). Handles searching, sorting, date grouping, and chat
create/rename/delete/select operations. Wires widget signals via ``findChild()``
and emits ``chat_selected`` when the user picks a chat.
"""

import uuid
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, Qt, QTimer, Signal, QSize, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QFrame, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMenu, QMessageBox,
)

from ..models import Chat, default_chat_name
from ..themes import get_colors
from ..views.panel.ui_side_panel import Ui_SidePanel
from ..views.widget.ui_chat_item import Ui_ChatItem


class _ChatItemClickFilter(QObject):
    """Select a chat on click or start inline rename on double-click."""

    def __init__(
        self,
        controller: "SidePanelController",
        chat: Chat,
        frame: QFrame,
        overflow_button: QPushButton,
    ):
        super().__init__(frame)
        self._controller = controller
        self._chat = chat
        self._frame = frame
        self._overflow_button = overflow_button

    def _is_overflow_click(self, watched: QObject, event: QEvent) -> bool:
        pos = event.pos()
        if watched is not self._frame:
            if not isinstance(watched, QWidget):
                return False
            if not self._frame.isAncestorOf(watched):
                # #region agent log
                from bookworm.debug_session_log import debug_log

                debug_log(
                    "side_panel_controller.py:_is_overflow_click",
                    "skipped mapFrom - not in hierarchy",
                    {"watched": type(watched).__name__},
                    hypothesis_id="F",
                )
                # #endregion
                return False
            pos = self._frame.mapFrom(watched, pos)
        return self._frame.childAt(pos) is self._overflow_button

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonDblClick:
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            if self._is_overflow_click(watched, event):
                return False
            self._controller.start_inline_rename(self._chat)
            return True

        if event.type() != QEvent.Type.MouseButtonPress:
            return False
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if self._is_overflow_click(watched, event):
            return False

        self._controller.chat_selected.emit(self._chat)
        return True


class _InlineRenameKeyFilter(QObject):
    """Commit inline rename on Enter, cancel on Escape."""

    def __init__(self, controller: "SidePanelController"):
        super().__init__()
        self._controller = controller

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.KeyPress:
            return False
        key_event = event
        if not isinstance(key_event, QKeyEvent):
            return False
        if key_event.key() == Qt.Key.Key_Escape:
            self._controller.cancel_inline_rename()
            return True
        if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._controller.commit_inline_rename()
            return True
        return False


class SidePanelController(QObject):
    """
    Controller for the side panel.

    Features:
    - Create, rename, delete, and switch chats
    - Search functionality
    - Sorting by name, date created, or date modified
    - Date grouping for chronological view

    Chat row layout lives in ``views/widget/chat_item.ui`` (one template per
    row). ``side_panel.ui`` only holds the empty ``QListWidget``; names are
    filled at runtime from ``Chat`` data.
    """

    CHAT_ITEM_HEIGHT = 28
    CHAT_ITEM_SPACING = 2

    chat_selected = Signal(object)
    chat_created = Signal(object)
    chat_renamed = Signal(object)
    chat_deleted = Signal(object)
    theme_toggle_requested = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.colors = get_colors(config.theme)
        self.chats: List[Chat] = []
        self.filtered_chats: List[Chat] = []
        self.current_sort = "date_modified"
        self.search_filter = ""
        self.active_chat_id: Optional[str] = None
        self._editing_chat: Optional[Chat] = None
        self._editing_frame: Optional[QFrame] = None
        self._editing_original_name = ""
        self._inline_rename_key_filter = _InlineRenameKeyFilter(self)

        self.widget = QWidget()
        self.ui = Ui_SidePanel()
        self.ui.setupUi(self.widget)

        self.theme_button = self.widget.findChild(QPushButton, "themeButton")
        self.search_input = self.widget.findChild(QLineEdit, "searchInput")
        self.sort_button = self.widget.findChild(QPushButton, "sortButton")
        self.new_chat_btn = self.widget.findChild(QPushButton, "newChatButton")
        self.chat_list = self.widget.findChild(QListWidget, "chatList")

        self.ui.panelLayout.setStretch(2, 1)

        self.search_input.textChanged.connect(self.on_search_changed)
        self.sort_button.clicked.connect(self.on_sort_button_clicked)
        self.new_chat_btn.clicked.connect(self.on_new_chat_clicked)
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)
        self.chat_list.itemClicked.connect(self.on_chat_clicked)

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.apply_search_filter)

        self._apply_styles()
        self.update_chat_list()

    def _apply_styles(self):
        c = self.colors
        self.widget.setStyleSheet(f"background-color: {c['bg_secondary']};")
        self.theme_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_tertiary']};
            }}
        """)
        self.theme_button.setText(f"Toggle Theme {self._theme_icon()}")
        self.sort_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                font-size: 16px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_tertiary']};
            }}
        """)
        self.new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_primary']};
                color: {c['accent']};
                border: 1px solid {c['border']};
                border-radius: 18px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_tertiary']};
            }}
        """)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 6px 8px;
            }}
        """)
        self.chat_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px 8px;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
        """)

    def _theme_icon(self) -> str:
        return "\U0001f383"

    def apply_theme(self, theme_name: str):
        self.config.theme = theme_name
        self.colors = get_colors(theme_name)
        self._apply_styles()
        self.update_chat_display()

    def set_active_chat_id(self, chat_id: Optional[str]):
        if chat_id == self.active_chat_id:
            return
        # #region agent log
        from bookworm.debug_session_log import debug_log

        debug_log(
            "side_panel_controller.py:set_active_chat_id",
            "update highlight only",
            {"chat_id": chat_id},
            hypothesis_id="F",
        )
        # #endregion
        self.active_chat_id = chat_id
        self._update_active_chat_highlight()

    def _chat_item_stylesheet(self, is_active: bool) -> str:
        c = self.colors
        border = c["accent"] if is_active else c["border"]
        return f"""
            QFrame#chatItemFrame {{
                background-color: {c['bg_primary']};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QLabel#nameLabel {{
                color: {c['text_primary']};
                background: transparent;
                padding: 0px;
            }}
            QLineEdit#nameEdit {{
                color: {c['text_primary']};
                background-color: {c['bg_primary']};
                border: 1px solid {c['accent']};
                border-radius: 2px;
                padding: 0px 2px;
            }}
            QPushButton#overflowMenuButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: none;
                border-radius: 4px;
                padding: 0px;
                font-size: 16px;
            }}
            QPushButton#overflowMenuButton:hover {{
                background-color: {c['bg_tertiary']};
                color: {c['text_primary']};
            }}
        """

    def _apply_chat_item_style(self, frame: QFrame, is_active: bool) -> None:
        frame.setStyleSheet(self._chat_item_stylesheet(is_active))

    def _update_active_chat_highlight(self) -> None:
        """Restyle list rows for the active chat without rebuilding the list."""
        for index in range(self.chat_list.count()):
            item = self.chat_list.item(index)
            if item is None or not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                continue
            chat = item.data(Qt.ItemDataRole.UserRole)
            if not chat:
                continue
            widget = self.chat_list.itemWidget(item)
            if isinstance(widget, QFrame):
                self._apply_chat_item_style(widget, chat.id == self.active_chat_id)
            if chat.id == self.active_chat_id:
                self.chat_list.setCurrentItem(item)

    def update_chat_list(self, chats: Optional[List[Chat]] = None):
        """Update the chat list with new chats."""
        if chats is not None:
            self.chats = chats
        self.apply_sorting_and_filtering()

    def apply_sorting_and_filtering(self):
        """Apply sorting and filtering to the chat list."""
        filtered = self.chats
        if self.search_filter:
            filtered = [
                chat for chat in filtered
                if self.search_filter.lower() in chat.name.lower()
            ]

        if self.current_sort == "date_created":
            filtered.sort(key=lambda chat: chat.created_at, reverse=True)
        elif self.current_sort == "date_modified":
            filtered.sort(key=lambda chat: chat.updated_at, reverse=True)
        else:
            filtered.sort(key=lambda chat: chat.name.lower())

        self.filtered_chats = filtered
        self.update_chat_display()

    def update_chat_display(self):
        """Update the chat list widget with filtered chats."""
        if self._editing_chat is not None:
            self.commit_inline_rename()

        self.chat_list.clear()

        grouped_chats = self.group_chats_by_date(self.filtered_chats)

        for date, chats in grouped_chats.items():
            date_item = QListWidgetItem(f"  {date}")
            date_item.setFlags(Qt.ItemFlag.NoItemFlags)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            font = date_item.font()
            font.setBold(True)
            date_item.setFont(font)
            self.chat_list.addItem(date_item)

            for chat in chats:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, chat)
                item.setToolTip(
                    f"Created: {chat.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Modified: {chat.updated_at.strftime('%Y-%m-%d %H:%M')}"
                )
                item_widget = self._create_chat_item_widget(chat)
                row_height = self.CHAT_ITEM_HEIGHT + self.CHAT_ITEM_SPACING
                item.setSizeHint(QSize(0, row_height))
                self.chat_list.addItem(item)
                self.chat_list.setItemWidget(item, item_widget)

                if chat.id == self.active_chat_id:
                    self.chat_list.setCurrentItem(item)

    def _create_chat_item_widget(self, chat: Chat) -> QFrame:
        """Build a chat item widget from ui_chat_item for the list row."""
        frame = QFrame()
        item_ui = Ui_ChatItem()
        item_ui.setupUi(frame)
        frame.setFixedHeight(self.CHAT_ITEM_HEIGHT)

        self._apply_chat_item_style(frame, chat.id == self.active_chat_id)

        name_label = frame.findChild(QLabel, "nameLabel")
        name_label.setText(chat.name)
        name_edit = frame.findChild(QLineEdit, "nameEdit")
        name_edit.setVisible(False)
        name_edit.editingFinished.connect(
            lambda _chat=chat: self._on_inline_rename_editing_finished(_chat)
        )

        overflow_button = frame.findChild(QPushButton, "overflowMenuButton")
        overflow_button.setCursor(Qt.CursorShape.PointingHandCursor)
        overflow_button.clicked.connect(
            lambda _checked=False, c=chat, btn=overflow_button: (
                self._on_overflow_menu_clicked(c, btn)
            )
        )

        click_filter = _ChatItemClickFilter(self, chat, frame, overflow_button)
        frame.installEventFilter(click_filter)
        name_label.installEventFilter(click_filter)

        return frame

    def _on_overflow_menu_clicked(self, chat: Chat, button: QPushButton) -> None:
        """Show rename/delete actions from the overflow menu button."""
        menu = self._build_chat_actions_menu(chat)
        menu.popup(button.mapToGlobal(button.rect().bottomLeft()))

    def _build_chat_actions_menu(self, chat: Chat) -> QMenu:
        """Build the rename/delete menu for a chat."""
        menu = QMenu(self.widget)

        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(lambda: self.start_inline_rename(chat))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_chat(chat))

        return menu

    def group_chats_by_date(self, chats: List[Chat]) -> Dict[str, List[Chat]]:
        """Group chats by date for display."""
        groups: Dict[str, List[Chat]] = {}

        for chat in chats:
            now = datetime.now()
            delta = now - chat.updated_at

            if delta < timedelta(days=1):
                date_key = "Today"
            elif delta < timedelta(days=2):
                date_key = "Yesterday"
            elif delta < timedelta(days=7):
                date_key = chat.updated_at.strftime("%A")
            elif delta < timedelta(days=30):
                date_key = chat.updated_at.strftime("%B %d")
            else:
                date_key = "Older"

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(chat)

        sorted_groups: Dict[str, List[Chat]] = {}
        for date_key in sorted(groups.keys(), key=lambda x: (
            99 if x == "Older" else
            0 if x == "Today" else
            1 if x == "Yesterday" else
            2
        )):
            sorted_groups[date_key] = groups[date_key]

        return sorted_groups

    def on_sort_button_clicked(self):
        """Show sort options menu."""
        menu = QMenu(self.widget)
        sort_options = [
            ("date_modified", "Date Modified"),
            ("date_created", "Date Created"),
            ("name", "Name"),
        ]
        for sort_key, label in sort_options:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.current_sort == sort_key)
            action.triggered.connect(
                lambda checked, key=sort_key: self._set_sort(key)
            )
        menu.popup(self.sort_button.mapToGlobal(
            self.sort_button.rect().bottomLeft()
        ))

    def _set_sort(self, sort_key: str):
        self.current_sort = sort_key
        self.apply_sorting_and_filtering()

    def on_search_changed(self, text: str):
        """Handle search input changes."""
        self.search_filter = text
        self.search_timer.start(self.config.search_delay)

    def apply_search_filter(self):
        """Apply the search filter."""
        self.apply_sorting_and_filtering()

    def on_new_chat_clicked(self):
        """Handle new chat button click."""
        now = datetime.now()
        new_chat = Chat(
            chat_id=str(uuid.uuid4()),
            name=default_chat_name(now),
            created_at=now,
            updated_at=now,
            messages=[]
        )
        self.chat_created.emit(new_chat)

    def on_chat_clicked(self, item: QListWidgetItem):
        """Handle chat selection."""
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEnabled:
            chat = item.data(Qt.ItemDataRole.UserRole)
            if chat:
                self.chat_selected.emit(chat)

    def start_inline_rename(self, chat: Chat) -> None:
        """Replace the chat name label with an inline editor."""
        if self._editing_chat is not None and self._editing_chat.id != chat.id:
            self.commit_inline_rename()

        for index in range(self.chat_list.count()):
            item = self.chat_list.item(index)
            if item is None or not (item.flags() & Qt.ItemFlag.ItemIsEnabled):
                continue
            item_chat = item.data(Qt.ItemDataRole.UserRole)
            if item_chat and item_chat.id == chat.id:
                widget = self.chat_list.itemWidget(item)
                if isinstance(widget, QFrame):
                    self._begin_inline_rename(chat, widget)
                return

    def _begin_inline_rename(self, chat: Chat, frame: QFrame) -> None:
        name_label = frame.findChild(QLabel, "nameLabel")
        name_edit = frame.findChild(QLineEdit, "nameEdit")
        if name_label is None or name_edit is None:
            return

        self._editing_chat = chat
        self._editing_frame = frame
        self._editing_original_name = chat.name

        name_edit.setText(chat.name)
        name_label.hide()
        name_edit.show()
        name_edit.setFocus()
        name_edit.selectAll()
        name_edit.installEventFilter(self._inline_rename_key_filter)

    def _on_inline_rename_editing_finished(self, chat: Chat) -> None:
        if self._editing_chat is None or self._editing_chat.id != chat.id:
            return
        self.commit_inline_rename()

    def commit_inline_rename(self) -> None:
        """Save the inline rename and restore the label."""
        if self._editing_chat is None or self._editing_frame is None:
            return

        chat = self._editing_chat
        frame = self._editing_frame
        name_edit = frame.findChild(QLineEdit, "nameEdit")
        if name_edit is None:
            self._clear_inline_rename_state()
            return

        new_name = name_edit.text().strip()
        self._finish_inline_rename_ui(frame, name_edit)

        if not new_name or new_name == self._editing_original_name:
            chat.name = self._editing_original_name
            return

        chat.name = new_name
        chat.updated_at = datetime.now()
        self.chat_renamed.emit(chat)

    def cancel_inline_rename(self) -> None:
        """Discard inline rename edits and restore the label."""
        if self._editing_chat is None or self._editing_frame is None:
            return

        chat = self._editing_chat
        chat.name = self._editing_original_name
        frame = self._editing_frame
        name_edit = frame.findChild(QLineEdit, "nameEdit")
        if name_edit is not None:
            self._finish_inline_rename_ui(frame, name_edit)

    def _finish_inline_rename_ui(self, frame: QFrame, name_edit: QLineEdit) -> None:
        name_label = frame.findChild(QLabel, "nameLabel")
        name_edit.removeEventFilter(self._inline_rename_key_filter)
        name_edit.hide()
        if name_label is not None:
            name_label.setText(self._editing_chat.name if self._editing_chat else "")
            name_label.show()
        self._clear_inline_rename_state()

    def _clear_inline_rename_state(self) -> None:
        self._editing_chat = None
        self._editing_frame = None
        self._editing_original_name = ""

    def delete_chat(self, chat: Chat):
        """Delete a chat."""
        reply = QMessageBox.question(
            self.widget, "Delete Chat",
            f"Are you sure you want to delete the chat '{chat.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.chat_deleted.emit(chat)
