"""
Main Panel Controller

Owns the main panel view (``ui_main_panel``) and all chat behaviour:
rendering user bubbles, agent markdown, copy/redo actions, theme styling,
and the input area. Wires widget signals via ``findChild()``.
"""

from typing import List, Optional

from PySide6.QtCore import QObject, Qt, QTimer, Signal, QEvent
from PySide6.QtGui import QGuiApplication, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QLabel, QScrollArea, QFrame, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy,
)

from ..markdown_renderer import create_markdown_view, update_markdown_widget
from ..models import Message
from ..themes import get_colors
from ..views.panel.ui_main_panel import Ui_MainPanel


class MainPanelController(QObject):
    """Controller for the main panel chat interface."""

    messages_changed = Signal()
    draft_changed = Signal()
    agent_turn_requested = Signal()

    INPUT_MAX_HEIGHT = 120
    INPUT_STYLE_PADDING = 8
    MARKDOWN_DEBOUNCE_MS = 75

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.colors = get_colors(config.theme)
        self.messages: List[Message] = []
        self.is_processing = False
        self._agent_turn_in_progress = False
        self._streaming_message: Optional[Message] = None
        self._streaming_tool_calls: list = []
        self._suppress_layout_refresh = False
        self._active_markdown_views: set = set()

        self._markdown_update_timer = QTimer(self)
        self._markdown_update_timer.setSingleShot(True)
        self._markdown_update_timer.setInterval(self.MARKDOWN_DEBOUNCE_MS)
        self._markdown_update_timer.timeout.connect(self._flush_streaming_markdown)

        self._layout_refresh_timer = QTimer(self)
        self._layout_refresh_timer.setSingleShot(True)
        self._layout_refresh_timer.setInterval(0)
        self._layout_refresh_timer.timeout.connect(self._do_refresh_message_layouts)

        self.widget = QWidget()
        self.ui = Ui_MainPanel()
        self.ui.setupUi(self.widget)

        self.scroll_area = self.widget.findChild(QScrollArea, "scrollArea")
        self.message_container = self.widget.findChild(QWidget, "messageContainer")
        self.message_layout = self.widget.findChild(QVBoxLayout, "messageLayout")
        self.input_frame = self.widget.findChild(QFrame, "inputFrame")
        self.message_input = self.widget.findChild(QTextEdit, "messageInput")
        self.send_button = self.widget.findChild(QPushButton, "sendButton")

        self.ui.panelLayout.setStretch(0, 1)

        self.message_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._configure_message_input_document()
        self.ui.inputLayout.setAlignment(
            self.send_button, Qt.AlignmentFlag.AlignBottom
        )
        self.message_layout.addStretch()

        self._apply_styles()
        self._resize_message_input()
        self.message_input.textChanged.connect(self._on_message_input_changed)
        self.send_button.clicked.connect(self.on_send_clicked)
        self.scroll_area.installEventFilter(self)
        self.widget.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if (
            not self._suppress_layout_refresh
            and watched in (self.scroll_area, self.widget)
            and event.type() in (QEvent.Type.Show, QEvent.Type.Resize)
        ):
            self._layout_refresh_timer.start()
        return super().eventFilter(watched, event)

    def _message_content_max_width(self) -> int:
        for source in (self.scroll_area.viewport(), self.widget, self.scroll_area):
            width = source.width()
            if width > 0:
                return max(200, int(width * 0.65))
        return 480

    def refresh_message_layouts(self) -> None:
        """Schedule a single coalesced layout refresh."""
        self._layout_refresh_timer.start()

    def _do_refresh_message_layouts(self) -> None:
        """Recompute bubble widths and markdown heights after the panel is laid out."""
        max_width = self._message_content_max_width()
        for message in self.messages:
            if message.role == "user":
                bubble = getattr(message, "user_bubble", None)
                if bubble is not None:
                    bubble.setMaximumWidth(max_width)
            elif message.role == "assistant":
                browser = getattr(message, "markdown_browser", None)
                if browser is not None:
                    update_markdown_widget(
                        browser,
                        message.content,
                        self.colors,
                        is_valid=lambda v=browser: v in self._active_markdown_views,
                    )
        self.scroll_area.widget().updateGeometry()

    def _render_assistant_message(self, message: Message) -> None:
        browser = getattr(message, "markdown_browser", None)
        if browser is None:
            return
        update_markdown_widget(
            browser,
            message.content,
            self.colors,
            is_valid=lambda v=browser: v in self._active_markdown_views,
        )
        self.scroll_to_bottom()

    def _apply_styles(self):
        """Apply theme-dependent inline styles to the static widgets."""
        c = self.colors
        self.input_frame.setStyleSheet(
            f"background-color: {c['bg_primary']}; border-top: 1px solid {c['border']};"
        )
        self.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 5px;
                padding: 4px 8px;
            }}
        """)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: {c['accent_text']};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {c['bg_tertiary']};
                color: {c['text_secondary']};
            }}
        """)

    def _configure_message_input_document(self):
        """Remove default block margins that add a phantom extra line."""
        doc = self.message_input.document()
        doc.setDocumentMargin(0)
        cursor = QTextCursor(doc)
        block_format = cursor.blockFormat()
        block_format.setTopMargin(0)
        block_format.setBottomMargin(0)
        cursor.setBlockFormat(block_format)
        self.message_input.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    def _message_input_frame_height(self) -> int:
        """Height for a single-line input including frame and padding."""
        fm = self.message_input.fontMetrics()
        frame = self.message_input.frameWidth() * 2
        return fm.height() + frame + self.INPUT_STYLE_PADDING

    def _resize_message_input(self):
        """Grow the input with content, starting from a single-line height."""
        doc = self.message_input.document()
        viewport_width = max(0, self.message_input.viewport().width())
        doc.setTextWidth(viewport_width)

        if not self.message_input.toPlainText():
            content_height = self.message_input.fontMetrics().lineSpacing()
        else:
            content_height = int(doc.documentLayout().documentSize().height())

        frame = self.message_input.frameWidth() * 2
        new_height = max(
            self._message_input_frame_height(),
            min(content_height + frame + self.INPUT_STYLE_PADDING, self.INPUT_MAX_HEIGHT),
        )
        if new_height >= self.INPUT_MAX_HEIGHT:
            self.message_input.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )
        else:
            self.message_input.setVerticalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        self.message_input.setFixedHeight(new_height)

    def _on_message_input_changed(self):
        self._resize_message_input()
        self.draft_changed.emit()

    def get_draft(self) -> str:
        """Return the current unsent draft text in the message input."""
        return self.message_input.toPlainText()

    def set_draft(self, text: str) -> None:
        """Restore unsent draft text into the message input."""
        self.message_input.setPlainText(text)
        self._resize_message_input()

    def clear_messages(self):
        self._active_markdown_views.clear()
        self.messages.clear()
        self._streaming_message = None
        self._streaming_tool_calls = []
        while self.message_layout.count() > 0:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.message_layout.addStretch()
        self.scroll_area.update()

    def load_messages(self, messages: List[Message]) -> None:
        """Replace the panel with a full message list (batch render after layout)."""
        self._suppress_layout_refresh = True
        try:
            self.clear_messages()
            for message in messages:
                self.messages.append(message)
                self.display_message(message, render_markdown=False)
        except Exception:
            self._suppress_layout_refresh = False
            raise
        QTimer.singleShot(0, self._after_load_messages)

    def _after_load_messages(self) -> None:
        try:
            self.refresh_message_layouts()
            self.scroll_to_bottom()
        finally:
            self._suppress_layout_refresh = False

    def add_message(self, message: Message):
        """Add a message to the chat."""
        self.messages.append(message)
        self.display_message(message)
        self.scroll_to_bottom()
        self.messages_changed.emit()

    def get_message_dicts(self, include_streaming: bool = False):
        """Return the current conversation for persistence."""
        return [
            message.to_dict()
            for message in self.messages
            if include_streaming or message is not self._streaming_message
        ]

    def set_agent_turn_in_progress(self, in_progress: bool) -> None:
        """Keep send disabled globally while the agent runner is active."""
        self._agent_turn_in_progress = in_progress
        self._update_send_button()

    def _update_send_button(self) -> None:
        busy = self._agent_turn_in_progress or self.is_processing
        self.send_button.setEnabled(not busy)

    def cancel_inflight_agent_request(self) -> None:
        """Rollback panel streaming UI when a turn could not be started."""
        if not self.is_processing:
            return
        if self._streaming_message is not None:
            self._remove_message(self._streaming_message)
            self._streaming_message = None
        self._streaming_tool_calls = []
        self._markdown_update_timer.stop()
        self.is_processing = False
        self._update_send_button()

    def detach_inflight_agent_turn(self) -> None:
        """Drop streaming UI state when switching chats during a background turn."""
        self._markdown_update_timer.stop()
        self._streaming_message = None
        self._streaming_tool_calls = []
        self.is_processing = False
        self._update_send_button()

    def reattach_streaming_turn(self) -> None:
        """Resume panel streaming when returning to the chat that owns the active turn."""
        for message in reversed(self.messages):
            if message.role != "assistant":
                continue
            self._streaming_message = message
            self._streaming_tool_calls = list(message.tool_calls or [])
            self.is_processing = True
            self._update_send_button()
            self._flush_streaming_markdown(force=True)
            return

    def display_message(self, message: Message, render_markdown: bool = True):
        """Display a single message in the chat."""
        if message.role == "user":
            widget = self._create_user_message_widget(message)
        else:
            widget = self._create_assistant_message_widget(message)
        message.display_widget = widget
        self.message_layout.insertWidget(self.message_layout.count() - 1, widget)
        if message.role == "user":
            bubble = getattr(message, "user_bubble", None)
            if bubble is not None:
                bubble.setMaximumWidth(self._message_content_max_width())
        elif render_markdown:
            QTimer.singleShot(0, lambda m=message: self._render_assistant_message(m))

    def _format_timestamp(self, timestamp) -> str:
        return timestamp.strftime("%I:%M %p, %d/%m/%Y").lstrip("0").replace(" 0", " ")

    def _create_user_message_widget(self, message: Message) -> QWidget:
        """User message: right-aligned bubble with timestamp below."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        row = QHBoxLayout()
        row.addStretch()

        bubble = QLabel(message.content)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        c = self.colors
        bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {c['bubble_user_bg']};
                color: {c['bubble_user_text']};
                border: 1px solid {c['bubble_user_border']};
                border-radius: 12px;
                padding: 10px 14px;
            }}
        """)
        bubble.setMaximumWidth(self._message_content_max_width())
        message.user_bubble = bubble
        row.addWidget(bubble)
        layout.addLayout(row)

        timestamp_row = QHBoxLayout()
        timestamp_row.addStretch()
        timestamp = QLabel(self._format_timestamp(message.timestamp))
        timestamp.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: 11px; background: transparent;"
        )
        timestamp_row.addWidget(timestamp)
        layout.addLayout(timestamp_row)

        return container

    def _create_assistant_message_widget(self, message: Message) -> QWidget:
        """Agent message: markdown with copy/redo buttons below."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        browser = create_markdown_view()
        self._active_markdown_views.add(browser)
        message.markdown_browser = browser
        layout.addWidget(browser)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        copy_btn = QPushButton("\U0001f4cb Copy")
        redo_btn = QPushButton("\u21bb Redo")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_action_button(copy_btn)
        self._style_action_button(redo_btn)
        copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(message.content)
        )
        redo_btn.clicked.connect(
            lambda: self._redo_assistant_message(message)
        )
        actions.addWidget(copy_btn)
        actions.addWidget(redo_btn)
        actions.addStretch()
        layout.addLayout(actions)

        return container

    def _style_action_button(self, button: QPushButton):
        c = self.colors
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
            }}
            QPushButton:disabled {{
                color: {c['text_secondary']};
            }}
        """)

    def _copy_to_clipboard(self, text: str):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    def _remove_message(self, message: Message):
        """Remove a message from the model and its widget from the layout."""
        widget = getattr(message, "display_widget", None)
        if message in self.messages:
            self.messages.remove(message)
        if widget is not None:
            self.message_layout.removeWidget(widget)
            widget.deleteLater()
            message.display_widget = None
            message.markdown_browser = None
        self.messages_changed.emit()

    def _redo_assistant_message(self, message: Message):
        """Remove the agent response and request a new one from the agent."""
        if (
            self.is_processing
            or self._agent_turn_in_progress
            or message.role != "assistant"
        ):
            return
        if message not in self.messages:
            return

        self._remove_message(message)
        self._request_agent_response()

    def _request_agent_response(self):
        """Ask AppController to run the real agent for a response."""
        self.is_processing = True
        self._update_send_button()
        self.begin_streaming_agent_turn()
        self.agent_turn_requested.emit()

    def begin_streaming_agent_turn(self) -> None:
        """Create a placeholder assistant message for streamed output."""
        self._streaming_tool_calls = []
        self._streaming_message = Message(role="assistant", content="")
        self.add_message(self._streaming_message)

    def append_agent_text_delta(self, delta: str) -> None:
        """Append streamed assistant text and schedule a markdown refresh."""
        if not self._streaming_message or not delta:
            return
        self._streaming_message.content += delta
        self._schedule_streaming_markdown_update()

    def record_agent_tool_call_started(
        self,
        name: str,
        arguments: str,
        call_id: str,
    ) -> None:
        """Track tool execution metadata for future collapsible UI."""
        self._streaming_tool_calls.append(
            {
                "id": call_id,
                "name": name,
                "arguments": arguments,
            }
        )

    def record_agent_tool_result(self, call_id: str, output: str) -> None:
        """Attach tool output to the in-flight turn metadata."""
        for tool_call in self._streaming_tool_calls:
            if tool_call.get("id") == call_id:
                tool_call["result"] = output
                break

    def complete_streaming_agent_turn(
        self,
        content: str,
        tool_calls: list,
    ) -> None:
        """Finalize the streaming assistant message."""
        if self._streaming_message is not None:
            self._streaming_message.content = content
            self._streaming_message.tool_calls = tool_calls or self._streaming_tool_calls
            self._flush_streaming_markdown(force=True)
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._finish_agent_turn()
        self.messages_changed.emit()

    def fail_agent_turn(self, error: str) -> None:
        """Show an agent failure in the conversation."""
        if not self.is_processing:
            return

        if self._streaming_message is not None:
            partial = (self._streaming_message.content or "").strip()
            if partial:
                self._streaming_message.content = (
                    f"{partial}\n\n---\n\n**Error:** {error}"
                )
            else:
                self._streaming_message.content = f"Error: {error}"
            self._flush_streaming_markdown(force=True)
            self._streaming_message = None
            self._streaming_tool_calls = []
        else:
            self.add_message(
                Message(role="assistant", content=f"Error: {error}")
            )
        self._finish_agent_turn()
        self.messages_changed.emit()

    def _finish_agent_turn(self) -> None:
        self.is_processing = False
        self._update_send_button()

    def _schedule_streaming_markdown_update(self) -> None:
        self._markdown_update_timer.start(self.MARKDOWN_DEBOUNCE_MS)

    def _flush_streaming_markdown(self, force: bool = False) -> None:
        if not force:
            self._markdown_update_timer.stop()
        message = self._streaming_message
        browser = getattr(message, "markdown_browser", None) if message else None
        if message is None or browser is None:
            return
        update_markdown_widget(
            browser,
            message.content,
            self.colors,
            is_valid=lambda v=browser: v in self._active_markdown_views,
        )
        self.scroll_to_bottom()

    def apply_theme(self, theme_name: str):
        self.colors = get_colors(theme_name)
        self._apply_styles()

        saved = self.messages[:]
        self.messages = []
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._active_markdown_views.clear()
        self._suppress_layout_refresh = True
        try:
            while self.message_layout.count() > 0:
                item = self.message_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.message_layout.addStretch()
            self.scroll_area.update()

            for msg in saved:
                msg.display_widget = None
                msg.markdown_browser = None
                msg.user_bubble = None
                self.messages.append(msg)
                self.display_message(msg, render_markdown=False)
        finally:
            self._suppress_layout_refresh = False
        QTimer.singleShot(0, self.refresh_message_layouts)

    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_send_clicked(self):
        """Handle send button click."""
        if self.is_processing or self._agent_turn_in_progress:
            return

        content = self.message_input.toPlainText().strip()
        if not content:
            return

        user_message = Message(role="user", content=content)
        self.add_message(user_message)
        self.message_input.clear()
        self._resize_message_input()

        self._request_agent_response()
