"""Markdown rendering for agent messages in the GUI."""

import re
from typing import Callable, Dict, Optional
from PySide6.QtCore import QTimer

import markdown
from pygments.formatters import HtmlFormatter

from bookworm.gui.views.widget.markdown_view import MarkdownView

_MARKDOWN = markdown.Markdown(
    extensions=["fenced_code", "tables", "nl2br", "sane_lists", "codehilite"],
    extension_configs={
        "codehilite": {
            "guess_lang": False,
            "noclasses": False,
            "pygments_style": "default",
            "css_class": "highlight",
        }
    },
)


def build_markdown_document_css(colors: Dict[str, str]) -> str:
    """Return CSS for markdown body and Pygments code blocks."""
    pygments_css = HtmlFormatter(style="default").get_style_defs(".highlight")
    return f"""
        body {{
            color: {colors['text_primary']};
            background: transparent;
            font-family: sans-serif;
            font-size: 14px;
            margin: 0;
            padding: 0;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {colors['text_primary']};
            margin: 8px 0 4px 0;
        }}
        p, li {{
            color: {colors['text_primary']};
            margin: 4px 0;
        }}
        ul, ol {{
            margin: 4px 0;
            padding-left: 20px;
        }}
        ul {{
            list-style-type: disc;
        }}
        a {{
            color: {colors['accent']};
        }}
        blockquote {{
            color: {colors['text_secondary']};
            border-left: 3px solid {colors['border']};
            margin: 8px 0;
            padding-left: 10px;
        }}
        code {{
            background-color: {colors['code_bg']};
            color: {colors['code_text']};
            border-radius: 3px;
            padding: 1px 4px;
            font-family: monospace;
            font-size: 12px;
        }}
        pre {{
            background-color: {colors['code_bg']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            margin: 8px 0;
        }}
        th, td {{
            border: 1px solid {colors['border']};
            padding: 6px 8px;
        }}
        th {{
            background-color: {colors['bg_tertiary']};
        }}
        .highlight {{
            background-color: {colors['code_bg']};
            border-radius: 4px;
        }}
        {pygments_css}
    """


def _normalize_bullet_markers(content: str) -> str:
    """Convert asterisk list markers to hyphens (not inline **bold**)."""
    return re.sub(r"(?m)^(\s*)\*(?=\s+(?!\*))", r"\1-", content or "")


def render_markdown_html(content: str, colors: Dict[str, str]) -> str:
    """Convert markdown to a themed HTML document."""
    _MARKDOWN.reset()
    body = _MARKDOWN.convert(_normalize_bullet_markers(content))
    css = build_markdown_document_css(colors)
    return f"<!DOCTYPE html><html><head><style>{css}</style></head><body>{body}</body></html>"


def _is_embedded(view: MarkdownView) -> bool:
    """True when the view is attached to a visible top-level window."""
    window = view.window()
    return window is not None and window.isVisible()


def _adjust_view_height(view: MarkdownView) -> None:
    if not _is_embedded(view):
        return
    doc = view.document()
    height = int(doc.documentLayout().documentSize().height()) + 8
    view.setFixedHeight(max(height, 20))


def _schedule_view_height(view: MarkdownView) -> None:
    QTimer.singleShot(0, lambda: _adjust_view_height(view))


def _ensure_view_hooks(view: MarkdownView) -> None:
    if getattr(view, "_markdown_hooks_ready", False):
        return
    view.document().documentLayout().documentSizeChanged.connect(
        lambda _size: _schedule_view_height(view)
    )
    view._markdown_hooks_ready = True


def create_markdown_view() -> MarkdownView:
    """Create an empty read-only rich-text view (populate after adding to layout)."""
    return MarkdownView()


def update_markdown_widget(
    view: MarkdownView,
    content: str,
    colors: Dict[str, str],
    is_valid: Optional[Callable[[], bool]] = None,
) -> None:
    """Re-render markdown HTML and resize the widget."""
    def apply() -> None:
        if is_valid is not None and not is_valid():
            return
        if not _is_embedded(view):
            return
        _ensure_view_hooks(view)
        view.setHtml(render_markdown_html(content, colors))
        _adjust_view_height(view)

    if _is_embedded(view):
        apply()
    else:
        QTimer.singleShot(0, apply)

