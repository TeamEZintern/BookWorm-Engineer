COLOR_SCHEMES = {
    "light": {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#f0f0f0",
        "text_primary": "#000000",
        "text_secondary": "#666666",
        "bubble_user_bg": "#e3f2fd",
        "bubble_user_text": "#000000",
        "bubble_user_border": "#2196f3",
        "bubble_assist_bg": "#f5f5f5",
        "bubble_assist_text": "#000000",
        "bubble_assist_border": "#dddddd",
        "accent": "#007bff",
        "accent_hover": "#0056b3",
        "accent_text": "#ffffff",
        "border": "#dddddd",
        "code_bg": "#f4f4f4",
        "code_text": "#000000",
    },
    "dark": {
        "bg_primary": "#1e1e1e",
        "bg_secondary": "#252526",
        "bg_tertiary": "#333333",
        "text_primary": "#e0e0e0",
        "text_secondary": "#999999",
        "bubble_user_bg": "#263238",
        "bubble_user_text": "#e0e0e0",
        "bubble_user_border": "#4fc3f7",
        "bubble_assist_bg": "#2d2d2d",
        "bubble_assist_text": "#e0e0e0",
        "bubble_assist_border": "#444444",
        "accent": "#4fc3f7",
        "accent_hover": "#29b6f6",
        "accent_text": "#000000",
        "border": "#444444",
        "code_bg": "#1a1a1a",
        "code_text": "#e0e0e0",
    },
}


def get_colors(theme: str = "light") -> dict:
    return COLOR_SCHEMES.get(theme, COLOR_SCHEMES["light"])


def build_stylesheet(theme: str = "light") -> str:
    colors = get_colors(theme)
    return f"""
        QMainWindow, QWidget {{
            background-color: {colors["bg_primary"]};
            color: {colors["text_primary"]};
        }}
        QListWidget {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            border: none;
        }}
        QListWidget::item:selected {{
            background-color: transparent;
            color: {colors["text_primary"]};
            border-left: 3px solid {colors["accent"]};
        }}
        QLineEdit, QTextEdit {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
        }}
        QComboBox {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
            border-radius: 3px;
            padding: 3px 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            selection-background-color: {colors["accent"]};
            selection-color: {colors["accent_text"]};
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QPushButton {{
            background-color: {colors["accent"]};
            color: {colors["accent_text"]};
            border: none;
            border-radius: 5px;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {colors["accent_hover"]};
        }}
        QPushButton:disabled {{
            background-color: {colors["bg_tertiary"]};
            color: {colors["text_secondary"]};
        }}
        QScrollArea {{
            background-color: {colors["bg_primary"]};
            border: none;
        }}
        QScrollBar:vertical {{
            background: {colors["bg_secondary"]};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {colors["bg_tertiary"]};
            border-radius: 5px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {colors["accent"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QSplitter::handle {{
            background: {colors["border"]};
            width: 1px;
        }}
        QStatusBar {{
            background: {colors["bg_tertiary"]};
            color: {colors["text_secondary"]};
        }}
        QToolTip {{
            background-color: {colors["bg_secondary"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
        }}
    """
