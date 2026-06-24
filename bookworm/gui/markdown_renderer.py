"""Markdown rendering for agent messages in the GUI."""

from typing import Dict

import markdown
from pygments.formatters import HtmlFormatter

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


def render_markdown_html(content: str, colors: Dict[str, str]) -> str:
    """Convert markdown to a themed HTML document."""
    _MARKDOWN.reset()
    body = _MARKDOWN.convert(content or "")
    css = build_markdown_document_css(colors)
    return f"<!DOCTYPE html><html><head><style>{css}</style></head><body>{body}</body></html>"


def _adjust_browser_height(browser) -> None:
    doc = browser.document()
    height = int(doc.documentLayout().documentSize().height()) + 8
    browser.setFixedHeight(max(height, 20))


def _configure_browser(browser, colors: Dict[str, str]) -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame

    browser.setOpenExternalLinks(True)
    browser.setFrameShape(QFrame.Shape.NoFrame)
    browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    browser.setStyleSheet("background: transparent;")
    browser.document().setDocumentMargin(0)
    browser.document().documentLayout().documentSizeChanged.connect(
        lambda _size: _adjust_browser_height(browser)
    )


def create_markdown_widget(content: str, colors: Dict[str, str]):
    """Create a read-only markdown widget sized to its content."""
    from PySide6.QtWidgets import QTextBrowser

    browser = QTextBrowser()
    _configure_browser(browser, colors)
    update_markdown_widget(browser, content, colors)
    return browser


def update_markdown_widget(
    browser,
    content: str,
    colors: Dict[str, str],
) -> None:
    """Re-render markdown HTML and resize the widget."""
    browser.setHtml(render_markdown_html(content, colors))
    _adjust_browser_height(browser)
