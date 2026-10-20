import sys
import os
import sqlite3
import re
import tempfile
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QFormLayout, QComboBox, QMessageBox, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import markdown

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
        
        self.setWindowTitle("Research Paper Organizer — Progress 1")
        self.setGeometry(100, 100, 1200, 750)

        self.init_ui()
        self.load_notes_list()

    def init_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ------------------ LEFT COLUMN ------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        self.btn_new_note = QPushButton("+ New Note")
        self.btn_new_note.clicked.connect(self.create_new_note)
        left_layout.addWidget(self.btn_new_note)

        left_layout.addWidget(QLabel("<b>Saved Notes:</b>"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes by title or content...")
        self.search_input.textChanged.connect(self.load_notes_list)
        left_layout.addWidget(self.search_input)
        self.notes_list = QListWidget()
        self.notes_list.itemClicked.connect(self.on_note_selected)
        left_layout.addWidget(self.notes_list)

        self.btn_delete_note = QPushButton("Delete Note")
        self.btn_delete_note.setStyleSheet("background-color: #ff4d4d; color: white;")
        self.btn_delete_note.clicked.connect(self.delete_current_note)
        left_layout.addWidget(self.btn_delete_note)

        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)

        # ------------------ MIDDLE COLUMN ------------------
        middle_widget = QWidget()
        middle_layout = QVBoxLayout()

        middle_layout.addWidget(QLabel("Note Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter title here...")
        middle_layout.addWidget(self.title_input)

        editor_label_layout = QHBoxLayout()
        editor_label_layout.addWidget(QLabel("Markdown Editor:"))
        
        middle_layout.addLayout(editor_label_layout)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Type your research notes in markdown here...")
        self.editor.textChanged.connect(self.on_content_changed)
        self.editor.cursorPositionChanged.connect(self.sync_scroll_with_cursor)
        middle_layout.addWidget(self.editor)

        self.btn_save = QPushButton("Save Note")
        self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_note)
        middle_layout.addWidget(self.btn_save)

        middle_widget.setLayout(middle_layout)
        main_splitter.addWidget(middle_widget)

        # ------------------ RIGHT COLUMN ------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        preview_header_layout = QHBoxLayout()
        preview_header_layout.addWidget(QLabel("<b>Live Preview:</b>"))
        
        right_layout.addLayout(preview_header_layout)

        self.preview_view = QWebEngineView()
        right_layout.addWidget(self.preview_view, stretch=2)

        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([200, 400, 400])
        self.setCentralWidget(main_splitter)

        self.setup_initial_preview_html()

    def setup_initial_preview_html(self):
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                html {{ scroll-behavior: smooth; }}
                body {{
                    margin: 0;
                    padding: 15px;
                    font-family: 'Times New Roman', Times, serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
                    line-height: 1.6;
                    color: #24292e;
                    background-color: #ffffff;
                }}
                h1, h2, h3 {{ border-bottom: 1px solid #eaecef; padding-bottom: .3em; font-family: sans-serif; }}
                
                p {{
                    margin-bottom: 12px;
                    text-align: justify;
                    text-justify: inter-word;
                }}

                p:has(img) {{
                    text-align: center;
                    margin: 20px 0;
                    background: #fafafa;
                    padding: 12px;
                    border: 1px solid #e1e4e8;
                    border-radius: 6px;
                }}
                img {{
                    max-width: 80%;
                    max-height: 400px;
                    height: auto;
                    border-radius: 4px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin: 0 auto;
                    display: block;
                }}
                
                code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 85%; }}
                pre {{ background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; border: 1px solid #e1e4e8; }}
                blockquote {{ border-left: 4px solid #dfe2e5; margin: 0; padding-left: 1rem; color: #6a737d; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
                th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; text-align: left; }}
                th {{ background-color: #f6f8fa; }}
            </style>
        </head>
        <body>
            <div id="content"></div>
        </body>
        </html>
        """
        base_path = QUrl.fromLocalFile(os.getcwd() + "/")
        self.preview_view.setHtml(styled_html, baseUrl=base_path)

    # --- LOGIC & EVENT HANDLERS ---

    def load_notes_list(self, _search_text=None):
        self.notes_list.clear()
        search_text = self.search_input.text() if hasattr(self, "search_input") else ""
        notes = self.db.get_all_notes(search_text)
        for note_id, title in notes:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.notes_list.addItem(item)

    def create_new_note(self):
        self.current_note_id = None
        self.title_input.clear()
        self.editor.clear()
        self.update_live_preview()

    def save_note(self):
        title = self.title_input.text().strip()
        content = self.editor.toPlainText()

        if not title:
            QMessageBox.warning(self, "Validation Error", "Note title cannot be empty!")
            return

        try:
            if self.current_note_id is None:
                self.current_note_id = self.db.add_note(title, content)
                QMessageBox.information(self, "Success", "Note created successfully!")
            else:
                self.db.update_note(self.current_note_id, title, content)
                QMessageBox.information(self, "Success", "Note updated successfully!")

            self.load_notes_list()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save note: {e}")

    def on_note_selected(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = self.db.get_note(note_id)
        if note:
            self.current_note_id = note_id
            self.title_input.setText(note[0])
            self.editor.setPlainText(note[1])
            self.update_live_preview()

    def delete_current_note(self):
        if self.current_note_id is None:
            QMessageBox.warning(self, "Selection Error", "Please select a note to delete.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_note(self.current_note_id)
            self.create_new_note()
            self.load_notes_list()

    def on_content_changed(self):
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

        # 1. Convert Markdown to HTML First
        html_body = markdown.markdown(text, extensions=['fenced_code', 'tables', 'nl2br'])

        # 2. Process [flow] shortcode after Markdown conversion
        def replace_flow(match):
            content = match.group(1).strip()
            items = [re.sub(r'<[^>]+>', '', item).strip() for item in re.split(r'<br\s*/?>|\n', content) if item.strip()]
            flow_html = '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 25px 0; font-family: sans-serif;">'
            for i, item in enumerate(items):
                flow_html += f'<div style="font-weight: bold; font-size: 16px; color: #1a1a1a; text-align: center;">{item}</div>'
                if i < len(items) - 1:
                    flow_html += '<div style="font-size: 22px; color: #333; margin: 4px 0; text-align: center; line-height: 1;">↓</div>'
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
                        <span style="border-bottom: 1.5px solid #000; padding: 0 8px 2px 8px; width: 100%; text-align: center;">{num}</span>
                        <span style="padding: 2px 8px 0 8px; width: 100%; text-align: center;">{den}</span>
                    </div>
                </div>
                '''
            else:
                return f'<div style="text-align: center; font-size: 18px; margin: 15px 0;"><i>{clean_content}</i></div>'

        # 4. Replace shortcodes on HTML text
        html_body = re.sub(r'\[flow\](.*?)\[/flow\]', replace_flow, html_body, flags=re.DOTALL | re.IGNORECASE)
        html_body = re.sub(r'\[math\](.*?)\[/math\]', replace_math, html_body, flags=re.DOTALL | re.IGNORECASE)

        # Escape special characters for JavaScript String insertion safely
        escaped_html = html_body.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', ' ')

        js_update = f"""
        document.getElementById('content').innerHTML = `{escaped_html}`;
        
        document.querySelectorAll('#content img').forEach((img, index) => {{
            let altText = img.getAttribute('alt') || 'Figure';
            if (!img.nextElementSibling || img.nextElementSibling.tagName !== 'FIGCAPTION') {{
                let caption = document.createElement('figcaption');
                caption.style.fontSize = '13px';
                caption.style.color = '#555';
                caption.style.marginTop = '8px';
                caption.style.fontStyle = 'italic';
                caption.innerText = `Figure ${{index + 1}}: ${{altText}}`;
                img.after(caption);
            }}
        }});
        """
        self.preview_view.page().runJavaScript(js_update)
        self.sync_scroll_with_cursor()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ResearchApp()
    window.show()
    sys.exit(app.exec())