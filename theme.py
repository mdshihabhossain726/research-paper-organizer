"""PART 2 - App look & feel (Member 2): colors and the Qt stylesheet (QSS)."""

# --- THEME ---------------------------------------------------------------
ACCENT = "#4f46e5"
ACCENT_HOVER = "#4338ca"
ACCENT_PRESSED = "#3730a3"

APP_QSS = """
QMainWindow { background: #f1f3f8; }
QWidget#root { background: #f1f3f8; }
QWidget { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; color: #1f2937; }

QFrame#card {
    background: #ffffff;
    border: 1px solid #e3e6ee;
    border-radius: 14px;
}

QLabel#brand { font-size: 15pt; font-weight: 700; color: #111827; padding: 2px 2px 6px 2px; }
QLabel#sectionTitle { font-size: 8pt; font-weight: 700; color: #6b7280; padding-top: 4px; }
QLabel#subtle { color: #6b7280; font-size: 9pt; }

QLineEdit {
    background: #ffffff;
    border: 1px solid #d9dde7;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #c7d2fe;
}
QLineEdit:focus { border: 1px solid #6366f1; }

QLineEdit#titleInput {
    font-size: 16pt;
    font-weight: 600;
    background: transparent;
    border: none;
    border-bottom: 1px solid #e3e6ee;
    border-radius: 0;
    padding: 4px 2px 8px 2px;
}
QLineEdit#titleInput:focus { border-bottom: 2px solid #6366f1; }

QTextEdit#editor {
    background: #fbfbfd;
    border: 1px solid #e3e6ee;
    border-radius: 10px;
    padding: 14px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11pt;
    selection-background-color: #c7d2fe;
}
QTextEdit#editor:focus { border: 1px solid #6366f1; }

QPushButton {
    background: #eef0f6;
    color: #1f2937;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 9px 14px;
    font-weight: 600;
}
QPushButton:hover { background: #e2e5ef; }
QPushButton:pressed { background: #d6dae6; }

QPushButton#primary {
    background: %(accent)s;
    color: #ffffff;
    padding: 10px 18px;
}
QPushButton#primary:hover { background: %(accent_hover)s; }
QPushButton#primary:pressed { background: %(accent_pressed)s; }

QPushButton#danger {
    background: transparent;
    color: #dc2626;
    border: 1px solid #fecaca;
}
QPushButton#danger:hover { background: #fef2f2; }
QPushButton#danger:pressed { background: #fee2e2; }

QListWidget#notesList { background: transparent; border: none; outline: 0; }
QListWidget#notesList::item {
    padding: 10px 12px;
    margin: 2px 0;
    border-radius: 8px;
}
QListWidget#notesList::item:hover { background: #f3f4f8; }
QListWidget#notesList::item:selected {
    background: #eef2ff;
    color: #3730a3;
    font-weight: 600;
}

QSplitter::handle { background: transparent; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #cfd4df; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #aab1c3; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QStatusBar { background: #f1f3f8; color: #6b7280; }
QStatusBar::item { border: none; }

QMessageBox { background: #ffffff; }
""" % {
    "accent": ACCENT,
    "accent_hover": ACCENT_HOVER,
    "accent_pressed": ACCENT_PRESSED,
}
