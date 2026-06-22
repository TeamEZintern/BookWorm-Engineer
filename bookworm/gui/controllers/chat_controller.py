"""
Chat Controller

Owns the chat panel view (``ui_chat_panel``) and all chat behaviour: rendering
user bubbles, agent markdown, copy/redo actions, theme styling, and the input
area. Wires widget signals via ``findChild()``.
"""

import re
from typing import List

from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QLabel, QScrollArea, QFrame, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy,
)

from ..models import Message
from ..themes import get_colors
from ..views.panel.ui_chat_panel import Ui_ChatPanel


class ChatController(QObject):
    """Controller for the main chat interface."""

    INPUT_MAX_HEIGHT = 120
    INPUT_STYLE_PADDING = 8

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.colors = get_colors(config.theme)
        self.messages: List[Message] = []
        self.is_processing = False

        self.widget = QWidget()
        self.ui = Ui_ChatPanel()
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
        self.message_input.textChanged.connect(self._resize_message_input)
        self.send_button.clicked.connect(self.on_send_clicked)

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

    def clear_messages(self):
        self.messages.clear()
        while self.message_layout.count() > 0:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.message_layout.addStretch()
        self.scroll_area.update()

    def add_message(self, message: Message):
        """Add a message to the chat."""
        self.messages.append(message)
        self.display_message(message)
        self.scroll_to_bottom()

    def display_message(self, message: Message):
        """Display a single message in the chat."""
        if message.role == "user":
            widget = self._create_user_message_widget(message)
        else:
            widget = self._create_assistant_message_widget(message)
        message.display_widget = widget
        self.message_layout.insertWidget(self.message_layout.count() - 1, widget)

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
        bubble.setMaximumWidth(int(self.widget.width() * 0.65) if self.widget.width() > 0 else 480)
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
        """Agent message: plain markdown with copy/redo buttons below."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        content = self.create_markdown_widget(message.content, self.colors)
        layout.addWidget(content)

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

    def _redo_assistant_message(self, message: Message):
        """Remove the agent response and request a new one from the agent."""
        if self.is_processing or message.role != "assistant":
            return
        if message not in self.messages:
            return

        self._remove_message(message)
        self._request_agent_response()

    def _request_agent_response(self):
        """Ask the agent for a response (simulated until backend is wired)."""
        self.is_processing = True
        self.send_button.setEnabled(False)
        # TODO: Send conversation history to agent and stream response
        QTimer.singleShot(1000, self.simulate_agent_response)

    def create_markdown_widget(self, content: str, colors: dict) -> QWidget:
        """Create a widget for displaying markdown content."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        cp = colors

        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                label = QLabel(f"<b>{line[2:]}</b>")
                label.setStyleSheet(
                    f"font-size: 18px; font-weight: bold; margin: 4px 0; "
                    f"color: {cp['text_primary']}; background: transparent;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('## '):
                label = QLabel(f"<b>{line[3:]}</b>")
                label.setStyleSheet(
                    f"font-size: 16px; font-weight: bold; margin: 4px 0; "
                    f"color: {cp['text_primary']}; background: transparent;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)
            elif re.match(r'^\d+\.\s', line):
                label = QLabel(line)
                label.setStyleSheet(
                    f"margin-left: 8px; margin-bottom: 2px; "
                    f"color: {cp['text_primary']}; background: transparent;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('- '):
                label = QLabel(f"\u2022 {line[2:]}")
                label.setStyleSheet(
                    f"margin-left: 15px; margin-bottom: 2px; "
                    f"color: {cp['text_primary']}; background: transparent;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('```'):
                code_label = QLabel(f"<pre>{line[3:]}</pre>")
                code_label.setStyleSheet(f"""
                    background-color: {cp['code_bg']};
                    color: {cp['code_text']};
                    border: 1px solid {cp['border']};
                    border-radius: 4px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 12px;
                """)
                code_label.setWordWrap(True)
                layout.addWidget(code_label)
            elif line.strip():
                label = QLabel(line)
                label.setStyleSheet(
                    f"color: {cp['text_primary']}; background: transparent;"
                )
                label.setWordWrap(True)
                layout.addWidget(label)

        return container

    def apply_theme(self, theme_name: str):
        self.colors = get_colors(theme_name)
        self._apply_styles()

        saved = self.messages[:]
        self.messages = []
        while self.message_layout.count() > 0:
            item = self.message_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.message_layout.addStretch()
        self.scroll_area.update()

        for msg in saved:
            msg.display_widget = None
            self.messages.append(msg)
            self.display_message(msg)

    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_send_clicked(self):
        """Handle send button click."""
        if self.is_processing:
            return

        content = self.message_input.toPlainText().strip()
        if not content:
            return

        user_message = Message(role="user", content=content)
        self.add_message(user_message)
        self.message_input.clear()
        self._resize_message_input()

        self._request_agent_response()

    def simulate_agent_response(self):
        """Simulate an agent response for testing."""
        agent_message = Message(
            role="assistant",
            content=(
                "This is a simulated agent response. In the real implementation, "
                "this would be the actual response from the Bookworm agent.\n\n"
                "1. First item\n"
                "2. Second item\n"
                "3. Third item"
            )
        )
        self.add_message(agent_message)

        self.is_processing = False
        self.send_button.setEnabled(True)
