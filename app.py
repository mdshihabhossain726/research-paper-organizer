"""PART 4 - Application core & logic (Member 4).

ResearchApp ties the parts together: it owns the state (current note, unsaved
changes) and the event handlers (new / save / open / delete note, search).
"""
import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from theme import APP_QSS
from database import DatabaseManager, get_data_directory
from ui_builder import UIBuilderMixin
from preview import PreviewMixin


class ResearchApp(UIBuilderMixin, PreviewMixin, QMainWindow):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_QSS)
    window = ResearchApp()
    window.show()
    sys.exit(app.exec())
