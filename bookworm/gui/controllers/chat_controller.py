"""
Chat Controller

Owns the chat panel view (``ui_chat_panel``) and all chat behaviour: rendering
message bubbles, markdown formatting, theme styling, the input area, and the
agent status indicator. Wires widget signals via ``findChild()``.
"""

from typing import List

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QWidget, QLabel, QScrollArea, QFrame, QTextEdit,
    QPushButton, QVBoxLayout, QSizePolicy,
)

from ..models import Message
from ..themes import get_colors
from ..views.panel.ui_chat_panel import Ui_ChatPanel
from ..views.widget.ui_message_bubble import Ui_MessageBubble


class ChatController(QObject):
    """
    Controller for the main chat interface.

    Features:
    - Message bubbles with markdown rendering
    - Tool execution blocks
    - Timestamp display
    - Message input area
    - Agent status indicator
    """

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.colors = get_colors(config.theme)
        self.messages: List[Message] = []
        self.is_processing = False

        self.widget = QWidget()
        self.ui = Ui_ChatPanel()
        self.ui.setupUi(self.widget)

        self.status_bar = self.widget.findChild(QLabel, "statusBar")
        self.scroll_area = self.widget.findChild(QScrollArea, "scrollArea")
        self.message_container = self.widget.findChild(QWidget, "messageContainer")
        self.message_layout = self.widget.findChild(QVBoxLayout, "messageLayout")
        self.input_frame = self.widget.findChild(QFrame, "inputFrame")
        self.message_input = self.widget.findChild(QTextEdit, "messageInput")
        self.send_button = self.widget.findChild(QPushButton, "sendButton")

        self.message_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.message_layout.addStretch()

        self._apply_styles()

        self.message_input.textChanged.connect(self.on_input_changed)
        self.send_button.clicked.connect(self.on_send_clicked)

    def _apply_styles(self):
        """Apply theme-dependent inline styles to the static widgets."""
        c = self.colors
        self.status_bar.setStyleSheet(
            f"background-color: {c['bg_tertiary']}; color: {c['text_secondary']}; "
            f"padding: 5px; border-bottom: 1px solid {c['border']};"
        )
        self.input_frame.setStyleSheet(
            f"background-color: {c['bg_secondary']}; color: {c['text_primary']}; "
            f"border-top: 1px solid {c['border']};"
        )
        self.message_input.setStyleSheet(
            f"background-color: {c['bg_secondary']}; color: {c['text_primary']}; "
            f"border: 1px solid {c['border']}; border-radius: 5px; padding: 5px;"
        )
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
        bubble = QFrame()
        bubble_ui = Ui_MessageBubble()
        bubble_ui.setupUi(bubble)
        bubble.setStyleSheet(self.get_message_style(message.role))

        role_label = bubble.findChild(QLabel, "roleLabel")
        role_label.setText(message.role.capitalize())
        role_label.setStyleSheet(
            f"font-weight: bold; font-size: 12px; color: {self.colors['text_primary']};"
        )

        timestamp_label = bubble.findChild(QLabel, "timestampLabel")
        timestamp_label.setText(message.timestamp.strftime("%H:%M"))
        timestamp_label.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 11px;"
        )

        content_layout = bubble.findChild(QVBoxLayout, "contentLayout")
        if message.role == "assistant":
            content_widget = self.create_markdown_widget(message.content, self.colors)
            content_layout.addWidget(content_widget)
        else:
            content_label = QLabel(message.content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(
                f"background-color: transparent; border: none; color: {self.colors['text_primary']};"
            )
            content_layout.addWidget(content_label)

        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble)

    def create_markdown_widget(self, content: str, colors: dict) -> QWidget:
        """Create a widget for displaying markdown content."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        cp = colors

        # Simple markdown rendering
        # In a real implementation, you would use a proper markdown renderer
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                label = QLabel(f"<h1>{line[2:]}</h1>")
                label.setStyleSheet(f"font-size: 18px; font-weight: bold; margin: 5px 0; color: {cp['text_primary']};")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('## '):
                label = QLabel(f"<h2>{line[3:]}</h2>")
                label.setStyleSheet(f"font-size: 16px; font-weight: bold; margin: 5px 0; color: {cp['text_primary']};")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('- '):
                label = QLabel(f"\u2022 {line[2:]}")
                label.setStyleSheet(f"margin-left: 15px; margin-bottom: 2px; color: {cp['text_primary']};")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('```'):
                # Code block
                code_label = QLabel(f"<pre><code>{line[3:]}</code></pre>")
                code_label.setStyleSheet(f"""
                    background-color: {cp['code_bg']};
                    color: {cp['code_text']};
                    border: 1px solid {cp['border']};
                    border-radius: 4px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 12px;
                    white-space: pre-wrap;
                """)
                code_label.setWordWrap(True)
                layout.addWidget(code_label)
            else:
                # Regular text
                if line.strip():
                    label = QLabel(line)
                    label.setStyleSheet(f"color: {cp['text_primary']};")
                    label.setWordWrap(True)
                    layout.addWidget(label)

        return container

    def get_message_style(self, role: str) -> str:
        """Get CSS style for message bubble based on role."""
        c = self.colors
        if role == "user":
            return f"""
                background-color: {c['bubble_user_bg']};
                color: {c['bubble_user_text']};
                border: 1px solid {c['bubble_user_border']};
                border-radius: 10px;
                margin-left: 20%;
            """
        else:
            return f"""
                background-color: {c['bubble_assist_bg']};
                color: {c['bubble_assist_text']};
                border: 1px solid {c['bubble_assist_border']};
                border-radius: 10px;
                margin-right: 20%;
            """

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
            self.messages.append(msg)
            self.display_message(msg)

    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_input_changed(self):
        """Handle input text changes."""
        document = self.message_input.document()
        new_height = min(max(30, int(document.size().height())), 100)
        self.message_input.setFixedHeight(new_height)

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

        self.is_processing = True
        self.status_bar.setText("Processing...")
        self.send_button.setEnabled(False)

        # TODO: Send message to agent and get response
        # For now, simulate a response
        QTimer.singleShot(1000, self.simulate_agent_response)

    def simulate_agent_response(self):
        """Simulate an agent response for testing."""
        agent_message = Message(
            role="assistant",
            content="This is a simulated agent response. In the real implementation, this would be the actual response from the Bookworm agent."
        )
        self.add_message(agent_message)

        self.is_processing = False
        self.status_bar.setText("Ready")
        self.send_button.setEnabled(True)
