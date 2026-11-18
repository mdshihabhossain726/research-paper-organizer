"""PART 1 - Database & data storage (Member 1).

SQLite notes database (create / read / update / delete / search) and the logic
that decides WHERE the database file lives (beside app.py, beside the .exe, or
in %LOCALAPPDATA% as a fallback).
"""
import os
import sys
import sqlite3
import tempfile


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
