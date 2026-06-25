import importlib.util
from pathlib import Path

_renderer_path = (
    Path(__file__).resolve().parents[1] / "bookworm" / "gui" / "markdown_renderer.py"
)
_spec = importlib.util.spec_from_file_location("markdown_renderer", _renderer_path)
_markdown_renderer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_markdown_renderer)

build_markdown_document_css = _markdown_renderer.build_markdown_document_css
render_markdown_html = _markdown_renderer.render_markdown_html

_LIGHT_COLORS = {
    "text_primary": "#000000",
    "text_secondary": "#666666",
    "accent": "#007bff",
    "border": "#dddddd",
    "code_bg": "#f4f4f4",
    "code_text": "#000000",
    "bg_tertiary": "#f0f0f0",
}

_DARK_COLORS = {
    "text_primary": "#e0e0e0",
    "text_secondary": "#999999",
    "accent": "#4fc3f7",
    "border": "#444444",
    "code_bg": "#1a1a1a",
    "code_text": "#e0e0e0",
    "bg_tertiary": "#333333",
}


def test_render_markdown_html_includes_heading():
    html = render_markdown_html("# Title", _LIGHT_COLORS)
    assert "<h1" in html
    assert "Title" in html


def test_render_markdown_html_includes_bold():
    html = render_markdown_html("This is **bold** text.", _LIGHT_COLORS)
    assert "<strong>bold</strong>" in html


def test_render_markdown_html_includes_fenced_code_and_pygments():
    content = "```python\nprint('hi')\n```"
    html = render_markdown_html(content, _DARK_COLORS)
    assert "highlight" in html
    assert "print" in html


def test_render_markdown_html_includes_table():
    content = "| A | B |\n|---|---|\n| 1 | 2 |"
    html = render_markdown_html(content, _LIGHT_COLORS)
    assert "<table>" in html
    assert "<td>1</td>" in html


def test_render_markdown_html_includes_link():
    html = render_markdown_html("[Docs](https://example.com)", _LIGHT_COLORS)
    assert 'href="https://example.com"' in html
    assert "Docs" in html


def test_render_markdown_html_converts_asterisk_bullets():
    html = render_markdown_html("* **Label:** value\n* item two", _LIGHT_COLORS)
    assert "<ul>" in html
    assert "<li>" in html
    assert "**Label:**" not in html
    assert "<strong>Label:</strong>" in html


def test_build_markdown_document_css_uses_theme_colors():
    css = build_markdown_document_css(_DARK_COLORS)
    assert "#e0e0e0" in css
    assert ".highlight" in css
