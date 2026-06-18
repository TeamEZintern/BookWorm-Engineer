"""
Chat Panel Component

This module implements the main chat interface for displaying messages and handling user input.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QScrollArea, QFrame, 
    QSizePolicy, QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
from PySide6.QtGui import QTextCursor, QTextDocument, QFont, QTextOption

from .config import GUIConfig
class Message:
    """Represents a message in the chat."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None,
                 tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.tool_calls = tool_calls or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tool_calls=data.get("tool_calls", [])
        )
class ChatPanel(QWidget):
    """
    Main chat interface for displaying messages and handling user input.
    
    Features:
    - Message bubbles with markdown rendering
    - Tool execution blocks
    - Timestamp display
    - Message input area
    - Agent status indicator
    """
    
    def __init__(self, config: GUIConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.messages: List[Message] = []
        self.is_processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-bottom: 1px solid #ddd;")
        self.status_bar.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.status_bar)
        
        # Message display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(10, 10, 10, 10)
        self.message_layout.setSpacing(10)
        self.message_layout.addStretch()
        
        self.scroll_area.setWidget(self.message_container)
        layout.addWidget(self.scroll_area, 1)
        
        # Input area
        self.input_frame = QFrame()
        self.input_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.input_frame.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        
        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setMaximumHeight(100)
        self.message_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.message_input.setStyleSheet("border-radius: 5px; padding: 5px;")
        self.message_input.textChanged.connect(self.on_input_changed)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.on_send_clicked)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button, 0)
        
        layout.addWidget(self.input_frame)
    
    def add_message(self, message: 'Message'):
        """Add a message to the chat."""
        self.messages.append(message)
        self.display_message(message)
        self.scroll_to_bottom()
    
    def display_message(self, message: Message):
        """Display a single message in the chat."""
        # Create message bubble container
        bubble_frame = QFrame()
        bubble_frame.setFrameStyle(QFrame.StyledPanel)
        bubble_frame.setStyleSheet(self.get_message_style(message.role))
        
        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(5)
        
        # Message header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        role_label = QLabel(message.role.capitalize())
        role_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(role_label)
        
        timestamp_label = QLabel(message.timestamp.strftime("%H:%M"))
        timestamp_label.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(timestamp_label, 1)
        
        bubble_layout.addLayout(header_layout)
        
        # Message content
        if message.role == "assistant":
            # Render markdown
            content_widget = self.create_markdown_widget(message.content)
            bubble_layout.addWidget(content_widget)
        else:
            # Plain text for user messages
            content_label = QLabel(message.content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("background-color: transparent; border: none;")
            bubble_layout.addWidget(content_label)
        
        # Add to message layout
        self.message_layout.insertWidget(self.message_layout.count() - 1, bubble_frame)
    
    def create_markdown_widget(self, content: str) -> QWidget:
        """Create a widget for displaying markdown content."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Simple markdown rendering
        # In a real implementation, you would use a proper markdown renderer
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                label = QLabel(f"<h1>{line[2:]}</h1>")
                label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 5px 0;")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('## '):
                label = QLabel(f"<h2>{line[3:]}</h2>")
                label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px 0;")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('- '):
                label = QLabel(f"• {line[2:]}")
                label.setStyleSheet("margin-left: 15px; margin-bottom: 2px;")
                label.setWordWrap(True)
                layout.addWidget(label)
            elif line.startswith('```'):
                # Code block
                code_label = QLabel(f"<pre><code>{line[3:]}</code></pre>")
                code_label.setStyleSheet("""
                    background-color: #f4f4f4;
                    border: 1px solid #ddd;
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
                    label.setWordWrap(True)
                    layout.addWidget(label)
        
        return container
    
    def get_message_style(self, role: str) -> str:
        """Get CSS style for message bubble based on role."""
        if role == "user":
            return """
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 10px;
                margin-left: 20%;
            """
        else:
            return """
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 10px;
                margin-right: 20%;
            """
    
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_input_changed(self):
        """Handle input text changes."""
        # Adjust height based on content
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
        
        # Add user message
        user_message = Message(role="user", content=content)
        self.add_message(user_message)
        
        # Clear input
        self.message_input.clear()
        
        # Set processing state
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
        
        # Reset processing state
        self.is_processing = False
        self.status_bar.setText("Ready")
        self.send_button.setEnabled(True)