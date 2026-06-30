"""
Main Panel Controller

Owns the main panel view (``ui_main_panel``) and all chat behaviour:
rendering user bubbles, agent markdown, copy/redo actions, theme styling,
and the input area. Wires widget signals via ``findChild()``.
"""

import json
from typing import List, Optional

from PySide6.QtCore import QObject, Qt, QTimer, Signal, QEvent, QPoint
from PySide6.QtGui import QGuiApplication, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QLabel, QScrollArea, QFrame, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy, QMenu, QToolButton,
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
    agent_turn_stop_requested = Signal()
    mode_change_requested = Signal(str)
    special_command_submitted = Signal(str)

    INPUT_MAX_HEIGHT = 120
    INPUT_STYLE_PADDING = 8

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.colors = get_colors(config.theme)
        self.messages: List[Message] = []
        self.is_processing = False
        self._agent_turn_in_progress = False
        self._streaming_message: Optional[Message] = None
        self._streaming_tool_calls: list = []
        self._streaming_reasoning = ""
        self._redo_buttons: List[QPushButton] = []
        self._suppress_layout_refresh = False
        self._active_markdown_views: set = set()

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
        self.mode_button = self.widget.findChild(QPushButton, "modeButton")
        self.send_button = self.widget.findChild(QPushButton, "sendButton")

        self.ui.panelLayout.setStretch(0, 1)

        self.message_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._configure_message_input_document()
        self.ui.inputLayout.setAlignment(
            self.send_button, Qt.AlignmentFlag.AlignBottom
        )
        self.ui.inputLayout.setAlignment(
            self.mode_button, Qt.AlignmentFlag.AlignBottom
        )
        self.message_layout.addStretch()

        self._apply_styles()
        self._resize_message_input()
        self.message_input.textChanged.connect(self._on_message_input_changed)
        self.mode_button.clicked.connect(self._show_mode_menu)
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

    def defer_layout_refresh(self) -> None:
        """Run a layout refresh on the next event-loop turn (after show/insert)."""
        QTimer.singleShot(0, self._do_refresh_message_layouts)

    def _do_refresh_message_layouts(self) -> None:
        """Recompute bubble widths and markdown heights after the panel is laid out."""
        max_width = self._message_content_max_width()
        for message in self.messages:
            if message.role == "user":
                bubble = getattr(message, "user_bubble", None)
                if bubble is not None:
                    bubble.setMaximumWidth(max_width)
            elif message.role == "assistant":
                for browser, content in getattr(message, "markdown_views", []):
                    update_markdown_widget(
                        browser,
                        content,
                        self.colors,
                        is_valid=lambda v=browser: v in self._active_markdown_views,
                    )
        self.scroll_area.widget().updateGeometry()

    def _render_assistant_message(self, message: Message) -> None:
        self._refresh_assistant_parts(message)
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
        self._style_mode_button()
        self._update_send_button()

    def _style_mode_button(self) -> None:
        c = self.colors
        self.mode_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['bg_tertiary']};
            }}
            QPushButton:disabled {{
                color: {c['text_secondary']};
            }}
        """)

    def update_mode(self, mode: str) -> None:
        self.mode_button.setText(f"Mode: {mode.capitalize()}")

    def _show_mode_menu(self) -> None:
        if self._agent_turn_in_progress:
            return
        menu = QMenu(self.mode_button)
        for mode in ("plan", "build", "research"):
            action = menu.addAction(mode.capitalize())
            action.triggered.connect(
                lambda checked=False, selected_mode=mode: self.mode_change_requested.emit(
                    selected_mode
                )
            )
        menu.adjustSize()
        menu_size = menu.sizeHint()
        button_top_left = self.mode_button.mapToGlobal(self.mode_button.rect().topLeft())
        window = self.widget.window()
        window_top_left = window.mapToGlobal(window.rect().topLeft())
        window_bottom_right = window.mapToGlobal(window.rect().bottomRight())

        x = min(
            max(button_top_left.x(), window_top_left.x()),
            window_bottom_right.x() - menu_size.width(),
        )
        y = max(window_top_left.y(), button_top_left.y() - menu_size.height())
        menu.exec(QPoint(x, y))

    def _style_send_button(self, is_stop: bool) -> None:
        c = self.colors
        if is_stop:
            background = "#dc3545"
            hover = "#c82333"
            text = "#ffffff"
        else:
            background = c["accent"]
            hover = c["accent_hover"]
            text = c["accent_text"]
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {background};
                color: {text};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
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
        self._redo_buttons.clear()
        self.messages.clear()
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
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
            self._do_refresh_message_layouts()
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
        """Toggle Stop/Send and redo availability while the agent runner is active."""
        self._agent_turn_in_progress = in_progress
        self.mode_button.setEnabled(not in_progress)
        self._update_send_button()
        self._update_redo_buttons()

    def _update_send_button(self) -> None:
        if self._agent_turn_in_progress:
            self.send_button.setText("Stop")
            self._style_send_button(is_stop=True)
            self.send_button.setEnabled(True)
            return
        self.send_button.setText("Send")
        self._style_send_button(is_stop=False)
        self.send_button.setEnabled(not self.is_processing)

    def _update_redo_buttons(self) -> None:
        enabled = not self._agent_turn_in_progress
        for button in self._redo_buttons:
            button.setEnabled(enabled)

    def cancel_inflight_agent_request(self) -> None:
        """Rollback panel streaming UI when a turn could not be started."""
        if not self.is_processing:
            return
        if self._streaming_message is not None:
            self._remove_message(self._streaming_message)
            self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
        self.is_processing = False
        self._update_send_button()

    def detach_inflight_agent_turn(self) -> None:
        """Drop streaming UI state when switching chats during a background turn."""
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
        self.is_processing = False
        self._update_send_button()

    def reattach_streaming_turn(self) -> None:
        """Resume panel streaming when returning to the chat that owns the active turn."""
        for message in reversed(self.messages):
            if message.role != "assistant":
                continue
            self._streaming_message = message
            self.is_processing = True
            self._update_send_button()
            self._refresh_assistant_parts(message)
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
        """Agent message: ordered reasoning/tool/final-answer parts with actions below."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        parts_layout = QVBoxLayout()
        parts_layout.setSpacing(6)
        message.parts_layout = parts_layout
        message.markdown_views = []
        message.part_widgets = []
        layout.addLayout(parts_layout)
        self._refresh_assistant_parts(message)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        copy_btn = QPushButton("\U0001f4cb Copy")
        redo_btn = QPushButton("\u21bb Redo")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_action_button(copy_btn)
        self._style_action_button(redo_btn)
        copy_btn.clicked.connect(
            lambda: self._copy_to_clipboard(message.text)
        )
        redo_btn.clicked.connect(
            lambda: self._redo_assistant_message(message)
        )
        if self._agent_turn_in_progress:
            redo_btn.setEnabled(False)
        message.redo_button = redo_btn
        self._redo_buttons.append(redo_btn)
        actions.addWidget(copy_btn)
        actions.addWidget(redo_btn)
        actions.addStretch()
        timestamp = QLabel(self._format_timestamp(message.timestamp))
        timestamp.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 11px; background: transparent;"
        )
        actions.addWidget(timestamp)
        layout.addLayout(actions)

        return container

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                self._active_markdown_views.discard(item.widget())
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _style_detail_text(self, text_view: QTextEdit) -> None:
        c = self.colors
        text_view.setReadOnly(True)
        text_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 6px;
                font-family: monospace;
                font-size: 12px;
            }}
        """)

    def _detail_height(self, text: str) -> int:
        line_count = max(2, min(12, text.count("\n") + 1))
        return min(220, line_count * self.message_input.fontMetrics().lineSpacing() + 24)

    def _create_collapsible_detail(self, title: str, body: str) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        toggle = QToolButton()
        toggle.setText(title)
        toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toggle.setArrowType(Qt.ArrowType.RightArrow)
        toggle.setCheckable(True)
        toggle.setChecked(False)
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {self.colors['text_secondary']};
                border: none;
                padding: 2px 0;
                font-weight: bold;
            }}
            QToolButton:hover {{
                color: {self.colors['text_primary']};
            }}
        """)

        detail = QTextEdit()
        self._style_detail_text(detail)
        detail.setPlainText(body)
        detail.setFixedHeight(self._detail_height(body))
        detail.setVisible(False)

        def on_toggled(checked: bool) -> None:
            toggle.setArrowType(
                Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
            )
            detail.setVisible(checked)
            self.refresh_message_layouts()

        toggle.toggled.connect(on_toggled)

        layout.addWidget(toggle)
        layout.addWidget(detail)
        container.bw_toggle = toggle
        container.bw_detail = detail
        container.bw_title = title
        container.bw_body = body
        return container

    def _update_collapsible_detail(self, container: QWidget, title: str, body: str) -> None:
        toggle = getattr(container, "bw_toggle", None)
        detail = getattr(container, "bw_detail", None)
        if toggle is None or detail is None:
            return
        if getattr(container, "bw_title", None) != title:
            toggle.setText(title)
            container.bw_title = title
        if getattr(container, "bw_body", None) != body:
            was_visible = detail.isVisible()
            detail.setPlainText(body)
            detail.setFixedHeight(self._detail_height(body))
            detail.setVisible(was_visible)
            container.bw_body = body

    def _format_jsonish_text(self, text: str) -> str:
        stripped = (text or "").strip()
        if not stripped:
            return "{}"
        try:
            return json.dumps(json.loads(stripped), indent=2)
        except json.JSONDecodeError:
            return stripped

    def _format_tool_call_detail(self, tool_call: dict, result: str | None = None) -> str:
        arguments = self._format_jsonish_text(tool_call.get("arguments", ""))
        result_text = result if result not in (None, "") else "Running..."
        return f"Arguments:\n{arguments}\n\nResult:\n{result_text}"

    def _tool_result_for(self, message: Message, call_id: str) -> str | None:
        for part in message.parts:
            if (
                part.get("type") == "tool_result"
                and part.get("tool_call_id") == call_id
            ):
                return part.get("content", "")
        return None

    def _create_final_answer_widget(self, text: str) -> QWidget:
        browser = create_markdown_view()
        self._active_markdown_views.add(browser)
        update_markdown_widget(
            browser,
            text,
            self.colors,
            is_valid=lambda v=browser: v in self._active_markdown_views,
        )
        return browser

    def _assistant_renderables(self, message: Message) -> list[dict]:
        renderables: list[dict] = []
        tool_index = 0
        for part_index, part in enumerate(message.parts):
            part_type = part.get("type")
            if part_type == "reasoning" and part.get("text", "").strip():
                renderables.append(
                    {
                        "type": "reasoning",
                        "key": f"reasoning:{part_index}",
                        "title": "Reasoning",
                        "body": part["text"].strip(),
                    }
                )
            elif part_type == "tool_call":
                tool_index += 1
                call_id = part.get("id", "")
                result = self._tool_result_for(message, call_id)
                status = "done" if result not in (None, "") else "running"
                renderables.append(
                    {
                        "type": "tool_call",
                        "key": f"tool_call:{call_id}",
                        "title": f"Tool {tool_index}: {part.get('name', 'tool')} ({status})",
                        "body": self._format_tool_call_detail(part, result),
                    }
                )
            elif part_type == "error_detail" and part.get("text", "").strip():
                renderables.append(
                    {
                        "type": "error_detail",
                        "key": f"error_detail:{part_index}",
                        "title": "Error details",
                        "body": part["text"].strip(),
                    }
                )
            elif part_type == "final_answer" and part.get("text"):
                renderables.append(
                    {
                        "type": "final_answer",
                        "key": f"final_answer:{part_index}",
                        "text": part["text"],
                    }
                )
        return renderables

    def _remove_rendered_part_widgets(
        self,
        parts_layout: QVBoxLayout,
        widgets: list[dict],
        start_index: int,
    ) -> None:
        for entry in widgets[start_index:]:
            widget = entry.get("widget")
            if widget is None:
                continue
            self._active_markdown_views.discard(widget)
            parts_layout.removeWidget(widget)
            widget.deleteLater()
        del widgets[start_index:]

    def _create_rendered_part_widget(self, renderable: dict) -> dict:
        if renderable["type"] == "final_answer":
            widget = self._create_final_answer_widget(renderable["text"])
            return {
                "type": renderable["type"],
                "key": renderable["key"],
                "widget": widget,
                "text": renderable["text"],
            }
        widget = self._create_collapsible_detail(
            renderable["title"],
            renderable["body"],
        )
        return {
            "type": renderable["type"],
            "key": renderable["key"],
            "widget": widget,
            "title": renderable["title"],
            "body": renderable["body"],
        }

    def _update_rendered_part_widget(self, entry: dict, renderable: dict) -> None:
        if renderable["type"] == "final_answer":
            if entry.get("text") == renderable["text"]:
                return
            browser = entry["widget"]
            update_markdown_widget(
                browser,
                renderable["text"],
                self.colors,
                is_valid=lambda v=browser: v in self._active_markdown_views,
            )
            entry["text"] = renderable["text"]
            return
        self._update_collapsible_detail(
            entry["widget"],
            renderable["title"],
            renderable["body"],
        )
        entry["title"] = renderable["title"]
        entry["body"] = renderable["body"]

    def _refresh_assistant_parts(self, message: Message) -> None:
        parts_layout = getattr(message, "parts_layout", None)
        if parts_layout is None:
            return
        renderables = self._assistant_renderables(message)
        rendered_widgets = getattr(message, "part_widgets", [])
        mismatch_at = None
        for index, renderable in enumerate(renderables):
            if index >= len(rendered_widgets):
                break
            entry = rendered_widgets[index]
            if (
                entry.get("type") != renderable["type"]
                or entry.get("key") != renderable["key"]
            ):
                mismatch_at = index
                break

        if mismatch_at is not None:
            self._remove_rendered_part_widgets(
                parts_layout,
                rendered_widgets,
                mismatch_at,
            )

        while len(rendered_widgets) > len(renderables):
            self._remove_rendered_part_widgets(
                parts_layout,
                rendered_widgets,
                len(renderables),
            )

        for index, renderable in enumerate(renderables):
            if index < len(rendered_widgets):
                self._update_rendered_part_widget(rendered_widgets[index], renderable)
                continue
            entry = self._create_rendered_part_widget(renderable)
            rendered_widgets.append(entry)
            parts_layout.addWidget(entry["widget"])

        message.part_widgets = rendered_widgets
        message.markdown_views = [
            (entry["widget"], entry.get("text", ""))
            for entry in rendered_widgets
            if entry.get("type") == "final_answer"
        ]

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
        redo_btn = getattr(message, "redo_button", None)
        if redo_btn in self._redo_buttons:
            self._redo_buttons.remove(redo_btn)
        widget = getattr(message, "display_widget", None)
        if message in self.messages:
            self.messages.remove(message)
        if widget is not None:
            self.message_layout.removeWidget(widget)
            widget.deleteLater()
            message.display_widget = None
            message.parts_layout = None
            message.markdown_views = []
            message.part_widgets = []
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
        self._streaming_reasoning = ""
        self._streaming_message = Message.assistant()
        self.add_message(self._streaming_message)

    def append_agent_text_delta(self, delta: str) -> None:
        """Append streamed assistant text and schedule a markdown refresh."""
        if not self._streaming_message or not delta:
            return
        self._streaming_message.append_final_answer_delta(delta)
        self._refresh_assistant_parts(self._streaming_message)
        self.scroll_to_bottom()

    def append_agent_reasoning_delta(self, delta: str) -> None:
        """Append streamed reasoning text into the assistant metadata section."""
        if not self._streaming_message or not delta:
            return
        self._streaming_reasoning += delta
        self._streaming_message.append_reasoning_delta(delta)
        self._refresh_assistant_parts(self._streaming_message)

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
        if self._streaming_message is not None:
            self._streaming_message.append_tool_call(call_id, name, arguments)
            self._refresh_assistant_parts(self._streaming_message)

    def record_agent_tool_result(self, call_id: str, output: str) -> None:
        """Attach tool output to the in-flight turn metadata."""
        for tool_call in self._streaming_tool_calls:
            if tool_call.get("id") == call_id:
                tool_call["result"] = output
                break
        if self._streaming_message is not None:
            self._streaming_message.append_tool_result(call_id, output)
            self._refresh_assistant_parts(self._streaming_message)

    def complete_streaming_agent_turn(
        self,
        content: str,
    ) -> None:
        """Finalize the streaming assistant message."""
        if self._streaming_message is not None:
            self._streaming_message.set_final_answer(content)
            self._refresh_assistant_parts(self._streaming_message)
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
        self._finish_agent_turn()
        self.messages_changed.emit()

    def finalize_stopped_agent_turn(self) -> None:
        """Keep partial streamed content when the user stops the agent."""
        if self._streaming_message is not None:
            if not self._streaming_message.parts:
                self._remove_message(self._streaming_message)
            else:
                self._refresh_assistant_parts(self._streaming_message)
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
        self._finish_agent_turn()
        self.messages_changed.emit()

    def _error_final_answer_text(self, error: str, partial: str = "") -> str:
        summary = (
            f"An error occurred: {error}. See stack trace above for details."
        )
        if partial:
            return f"{partial}\n\n{summary}"
        return summary

    def fail_agent_turn(self, error: str, error_detail: str | None = None) -> None:
        """Show an agent failure in the conversation."""
        if not self.is_processing:
            return

        detail = (error_detail or error).strip()
        if self._streaming_message is not None:
            partial = self._streaming_message.text.strip()
            if detail:
                self._streaming_message.append_error_detail(detail)
            self._streaming_message.set_final_answer(
                self._error_final_answer_text(error, partial)
            )
            self._refresh_assistant_parts(self._streaming_message)
            self._streaming_message = None
            self._streaming_tool_calls = []
            self._streaming_reasoning = ""
        else:
            content: list[dict] = []
            if detail:
                content.append({"type": "error_detail", "text": detail})
            content.append(
                {
                    "type": "final_answer",
                    "text": self._error_final_answer_text(error),
                }
            )
            self.add_message(Message(role="assistant", content=content))
        self._finish_agent_turn()
        self.messages_changed.emit()

    def _finish_agent_turn(self) -> None:
        self.is_processing = False
        self._update_send_button()

    def apply_theme(self, theme_name: str):
        self.colors = get_colors(theme_name)
        self._apply_styles()

        saved = self.messages[:]
        self.messages = []
        self._redo_buttons.clear()
        self._streaming_message = None
        self._streaming_tool_calls = []
        self._streaming_reasoning = ""
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
                msg.parts_layout = None
                msg.markdown_views = []
                msg.part_widgets = []
                msg.user_bubble = None
                self.messages.append(msg)
                self.display_message(msg, render_markdown=False)
        finally:
            self._suppress_layout_refresh = False
        self.defer_layout_refresh()

    def scroll_to_bottom(self):
        """Scroll the chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_send_clicked(self):
        """Handle send/stop button click."""
        if self._agent_turn_in_progress:
            self.agent_turn_stop_requested.emit()
            return
        if self.is_processing:
            return

        content = self.message_input.toPlainText().strip()
        if not content:
            return

        if content.startswith("/"):
            self.message_input.clear()
            self._resize_message_input()
            self.special_command_submitted.emit(content)
            return

        user_message = Message(role="user", content=content)
        self.add_message(user_message)
        self.message_input.clear()
        self._resize_message_input()

        self._request_agent_response()
