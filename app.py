import sys
import os
import sqlite3
import re
import tempfile
import markdown

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QMessageBox, QSplitter, QFrame,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWebEngineWidgets import QWebEngineView


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

PREVIEW_CSS = """
html { scroll-behavior: smooth; }
body {
    margin: 0;
    padding: 24px 28px 40px 28px;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: #1f2937;
    background: #ffffff;
}
h1, h2, h3, h4 { color: #111827; font-weight: 700; line-height: 1.3; margin: 1.5em 0 0.6em 0; }
h1 { font-size: 28px; padding-bottom: 0.3em; border-bottom: 2px solid #e5e7eb; }
h2 { font-size: 22px; padding-bottom: 0.25em; border-bottom: 1px solid #e5e7eb; }
h3 { font-size: 18px; }
h4 { font-size: 16px; }
p { margin: 0 0 14px 0; }
a { color: #4f46e5; text-decoration: none; }
ul, ol { padding-left: 24px; margin: 0 0 14px 0; }
li { margin-bottom: 4px; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 28px 0; }

p:has(img) {
    text-align: center;
    margin: 22px 0;
    background: #f9fafb;
    padding: 14px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
}
img {
    max-width: 80%;
    max-height: 400px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    display: block;
    margin: 0 auto;
}
figcaption {
    font-size: 13px;
    color: #6b7280;
    margin-top: 8px;
    font-style: italic;
    text-align: center;
}

code {
    background: #f3f4f6;
    color: #be185d;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 88%;
}
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 14px 16px;
    border-radius: 10px;
    overflow-x: auto;
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 13px;
    line-height: 1.5;
}
pre code { background: none; color: inherit; padding: 0; font-size: 100%; }

blockquote {
    border-left: 4px solid #6366f1;
    background: #f8fafc;
    margin: 16px 0;
    padding: 10px 16px;
    color: #475569;
    border-radius: 0 8px 8px 0;
}
blockquote p:last-child { margin-bottom: 0; }

table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }
th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
th { background: #f9fafb; font-weight: 600; }
tr:nth-child(even) td { background: #fcfcfd; }
"""

PREVIEW_SHELL = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>__CSS__</style>
</head>
<body>
    <div id="content"></div>
</body>
</html>
""".replace("__CSS__", PREVIEW_CSS)


# --- DATABASE MANAGER ---
class DatabaseManager:
    def __init__(self, db_name="research_notes.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Database Error: {e}")

    def add_note(self, title, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            conn.commit()
            return cursor.lastrowid

    def update_note(self, note_id, title, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE notes SET title = ?, content = ? WHERE id = ?", (title, content, note_id))
            conn.commit()

    def get_all_notes(self, search_text=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_text = search_text.strip()
            if search_text:
                pattern = f"%{search_text}%"
                cursor.execute(
                    "SELECT id, title FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC",
                    (pattern, pattern),
                )
            else:
                cursor.execute("SELECT id, title FROM notes ORDER BY id DESC")
            return cursor.fetchall()

    def get_note(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, content FROM notes WHERE id = ?", (note_id,))
            return cursor.fetchone()

    def delete_note(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()


# --- MAIN APPLICATION GUI ---
def get_data_directory():
    """Use a portable folder beside the EXE when writable; otherwise use LocalAppData."""
    if not getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(__file__))

    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    try:
        # Test whether the portable application folder is writable.
        fd, test_path = tempfile.mkstemp(prefix=".rpo_write_test_", dir=exe_dir)
        os.close(fd)
        os.remove(test_path)
        return exe_dir
    except OSError:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, "ResearchPaperOrganizer")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir


class ResearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_dir = get_data_directory()
        os.chdir(self.app_dir)
        self.db = DatabaseManager(os.path.join(self.app_dir, "research_notes.db"))
        self.current_note_id = None
        self._dirty = False

        self.setWindowTitle("Research Paper Organizer")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 620)

        self.init_ui()
        self.init_shortcuts()
        self.load_notes_list()
        self._set_dirty(False)

    # --- UI CONSTRUCTION ---

    def init_ui(self):
        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 14)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(14)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_editor_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([280, 540, 540])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

        self.status_info = QLabel()
        self.status_info.setObjectName("subtle")
        self.statusBar().addPermanentWidget(self.status_info)

        self.setup_initial_preview_html()

    def init_shortcuts(self):
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_note)
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self.create_new_note)

    def _make_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        return card, layout

    def _section_label(self, text):
        label = QLabel(text.upper())
        label.setObjectName("sectionTitle")
        return label

    def _build_sidebar(self):
        card, layout = self._make_card()

        brand = QLabel("Research Notes")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        self.btn_new_note = QPushButton("+  New note")
        self.btn_new_note.setObjectName("primary")
        self.btn_new_note.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_note.clicked.connect(self.create_new_note)
        layout.addWidget(self.btn_new_note)

        layout.addSpacing(6)
        layout.addWidget(self._section_label("Saved notes"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title or content…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.load_notes_list)
        layout.addWidget(self.search_input)

        self.notes_list = QListWidget()
        self.notes_list.setObjectName("notesList")
        self.notes_list.itemClicked.connect(self.on_note_selected)
        layout.addWidget(self.notes_list, stretch=1)

        self.btn_delete_note = QPushButton("Delete note")
        self.btn_delete_note.setObjectName("danger")
        self.btn_delete_note.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete_note.clicked.connect(self.delete_current_note)
        layout.addWidget(self.btn_delete_note)

        return card

    def _build_editor_panel(self):
        card, layout = self._make_card()

        layout.addWidget(self._section_label("Title"))
        self.title_input = QLineEdit()
        self.title_input.setObjectName("titleInput")
        self.title_input.setPlaceholderText("Untitled research note")
        self.title_input.textChanged.connect(lambda _text: self._set_dirty(True))
        layout.addWidget(self.title_input)

        header = QHBoxLayout()
        header.addWidget(self._section_label("Markdown"))
        header.addStretch()
        self.word_count_label = QLabel("0 words")
        self.word_count_label.setObjectName("subtle")
        header.addWidget(self.word_count_label)
        layout.addLayout(header)

        self.editor = QTextEdit()
        self.editor.setObjectName("editor")
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText(
            "Write your research notes in Markdown…\n\n"
            "Shortcodes: [flow]step one<br>step two[/flow]  and  [math]E = mc/2[/math]"
        )
        self.editor.textChanged.connect(self.on_content_changed)
        self.editor.cursorPositionChanged.connect(self.sync_scroll_with_cursor)
        layout.addWidget(self.editor, stretch=1)

        footer = QHBoxLayout()
        footer.addStretch()
        self.btn_save = QPushButton("Save note  (Ctrl+S)")
        self.btn_save.setObjectName("primary")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_note)
        footer.addWidget(self.btn_save)
        layout.addLayout(footer)

        return card

    def _build_preview_panel(self):
        card, layout = self._make_card()
        layout.addWidget(self._section_label("Live preview"))
        self.preview_view = QWebEngineView()
        layout.addWidget(self.preview_view, stretch=1)
        return card

    def setup_initial_preview_html(self):
        base_path = QUrl.fromLocalFile(os.getcwd() + "/")
        self.preview_view.setHtml(PREVIEW_SHELL, baseUrl=base_path)

    # --- STATE HELPERS ---

    def _set_dirty(self, dirty):
        self._dirty = dirty
        self._refresh_status()

    def _refresh_status(self):
        words = len(self.editor.toPlainText().split())
        self.word_count_label.setText(f"{words} word{'s' if words != 1 else ''}")
        if self._dirty:
            self.status_info.setText("●  Unsaved changes")
            self.status_info.setStyleSheet("color: #d97706; font-weight: 600;")
        else:
            self.status_info.setText("✓  All changes saved")
            self.status_info.setStyleSheet("")

    def _confirm_discard(self):
        if not self._dirty:
            return True
        choice = QMessageBox.question(
            self, "Unsaved changes",
            "You have unsaved changes. Discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return choice == QMessageBox.StandardButton.Yes

    def _reset_editor(self):
        self.current_note_id = None
        self.title_input.clear()
        self.editor.clear()
        self.notes_list.clearSelection()
        self.update_live_preview()
        self._set_dirty(False)

    # --- LOGIC & EVENT HANDLERS ---

    def load_notes_list(self, _search_text=None):
        self.notes_list.clear()
        notes = self.db.get_all_notes(self.search_input.text())
        for note_id, title in notes:
            item = QListWidgetItem(title or "Untitled")
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.notes_list.addItem(item)
            if note_id == self.current_note_id:
                self.notes_list.setCurrentItem(item)

    def create_new_note(self):
        if not self._confirm_discard():
            return
        self._reset_editor()
        self.title_input.setFocus()

    def save_note(self):
        title = self.title_input.text().strip()
        content = self.editor.toPlainText()

        if not title:
            QMessageBox.warning(self, "Missing title", "Please give your note a title before saving.")
            self.title_input.setFocus()
            return

        try:
            if self.current_note_id is None:
                self.current_note_id = self.db.add_note(title, content)
                message = "Note created"
            else:
                self.db.update_note(self.current_note_id, title, content)
                message = "Note updated"

            self._set_dirty(False)
            self.load_notes_list()
            self.statusBar().showMessage(f"{message} successfully", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save note: {e}")

    def on_note_selected(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        if note_id == self.current_note_id:
            return
        if not self._confirm_discard():
            self.load_notes_list()  # restore highlight to the open note
            return

        note = self.db.get_note(note_id)
        if note:
            self.current_note_id = note_id
            self.title_input.setText(note[0])
            self.editor.setPlainText(note[1] or "")
            self.update_live_preview()
            self._set_dirty(False)

    def delete_current_note(self):
        if self.current_note_id is None:
            QMessageBox.warning(self, "No note selected", "Please select a note to delete.")
            return

        confirm = QMessageBox.question(
            self, "Delete note",
            "Are you sure you want to delete this note? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_note(self.current_note_id)
            self._reset_editor()
            self.load_notes_list()
            self.statusBar().showMessage("Note deleted", 3000)

    def on_content_changed(self):
        self._set_dirty(True)
        self.update_live_preview()

    def sync_scroll_with_cursor(self):
        editor_scroll = self.editor.verticalScrollBar()
        if editor_scroll.maximum() > 0:
            ratio = editor_scroll.value() / editor_scroll.maximum()
            js_script = f"""
            var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            if (maxScroll > 0) {{
                window.scrollTo({{ top: maxScroll * {ratio}, behavior: 'smooth' }});
            }}
            """
            self.preview_view.page().runJavaScript(js_script)

    def update_live_preview(self):
        text = self.editor.toPlainText()

        # 1. Convert Markdown to HTML first
        html_body = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])

        # 2. Process [flow] shortcode after Markdown conversion
        def replace_flow(match):
            content = match.group(1).strip()
            items = [re.sub(r'<[^>]+>', '', item).strip() for item in re.split(r'<br\s*/?>|\n', content) if item.strip()]
            flow_html = '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 25px 0; font-family: \'Segoe UI\', sans-serif;">'
            for i, item in enumerate(items):
                flow_html += f'<div style="font-weight: 600; font-size: 16px; color: #111827; text-align: center; padding: 8px 18px; background: #eef2ff; border-radius: 8px;">{item}</div>'
                if i < len(items) - 1:
                    flow_html += '<div style="font-size: 20px; color: #6366f1; margin: 4px 0; text-align: center; line-height: 1;">↓</div>'
            flow_html += '</div>'
            return flow_html

        # 3. Process [math] shortcode after Markdown conversion
        def replace_math(match):
            content = match.group(1).strip()
            clean_content = re.sub(r'<[^>]+>', '', content)

            if '=' in clean_content:
                left, right = clean_content.split('=', 1)
                left = left.strip()
                right = right.strip()
            else:
                left, right = "", clean_content

            if '/' in right:
                num, den = right.split('/', 1)
                num = num.strip().strip('()')
                den = den.strip().strip('()')

                return f'''
                <div style="display: flex; align-items: center; justify-content: center; font-family: 'Times New Roman', serif; font-size: 18px; font-style: italic; margin: 18px 0;">
                    {f"<span>{left} &nbsp;=&nbsp;</span>" if left else ""}
                    <div style="display: inline-flex; flex-direction: column; align-items: center; text-align: center; padding: 0 4px;">
                        <span style="border-bottom: 1.5px solid #111827; padding: 0 8px 2px 8px; width: 100%; text-align: center;">{num}</span>
                        <span style="padding: 2px 8px 0 8px; width: 100%; text-align: center;">{den}</span>
                    </div>
                </div>
                '''
            else:
                return f'<div style="text-align: center; font-size: 18px; margin: 15px 0;"><i>{clean_content}</i></div>'

        # 4. Replace shortcodes on HTML text
        html_body = re.sub(r'\[flow\](.*?)\[/flow\]', replace_flow, html_body, flags=re.DOTALL | re.IGNORECASE)
        html_body = re.sub(r'\[math\](.*?)\[/math\]', replace_math, html_body, flags=re.DOTALL | re.IGNORECASE)

        # Escape for a JavaScript template literal. Newlines are kept so code blocks keep their line breaks.
        escaped_html = (
            html_body.replace('\r', '')
            .replace('\\', '\\\\')
            .replace('`', '\\`')
            .replace('$', '\\$')
        )

        js_update = f"""
        document.getElementById('content').innerHTML = `{escaped_html}`;

        document.querySelectorAll('#content img').forEach((img, index) => {{
            if (!img.nextElementSibling || img.nextElementSibling.tagName !== 'FIGCAPTION') {{
                const caption = document.createElement('figcaption');
                const altText = img.getAttribute('alt') || 'Figure';
                caption.innerText = `Figure ${{index + 1}}: ${{altText}}`;
                img.after(caption);
            }}
        }});
        """
        self.preview_view.page().runJavaScript(js_update)
        self.sync_scroll_with_cursor()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_QSS)
    window = ResearchApp()
    window.show()
    sys.exit(app.exec())
