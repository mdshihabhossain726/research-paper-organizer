"""Markdown editor with writing help (VS Code style).

* Type  /  then a word  ->  suggestion popup  (/h1, /table, /flow ...)
  Press Tab (or Enter) to insert the snippet.  Esc closes the popup.
* Ctrl+B / Ctrl+I / Ctrl+K  ->  bold / italic / link (wraps the selected text)
* Enter inside a list ("- item", "1. item")  ->  next item is added automatically;
  Enter on an empty item ends the list.
* `insert_snippet(key)` is also used by the toolbar buttons in ui_builder.py.

In SNIPPETS, "§" marks where the cursor ends up after insertion.
"""
import re

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QTextCursor, QKeySequence, QShortcut
from PyQt6.QtWidgets import QTextEdit, QCompleter

CURSOR = "§"

# key -> (description, text).  Keep keys lowercase, no spaces.
SNIPPETS = {
    "h1":        ("Heading 1",        "# §"),
    "h2":        ("Heading 2",        "## §"),
    "h3":        ("Heading 3",        "### §"),
    "bold":      ("Bold",             "**§**"),
    "italic":    ("Italic",           "*§*"),
    "code":      ("Inline code",      "`§`"),
    "codeblock": ("Code block",       "```\n§\n```"),
    "list":      ("Bullet list",      "- §"),
    "numbered":  ("Numbered list",    "1. §"),
    "quote":     ("Quote",            "> §"),
    "link":      ("Link",             "[text](https://§)"),
    "image":     ("Image",            "![alt text](images/§)"),
    "line":      ("Horizontal line",  "\n---\n§"),
    "table":     ("Table",            "| Column 1 | Column 2 |\n| --- | --- |\n| § | |"),
    "flow":      ("Flow diagram",     "[flow]\n§Step one<br>Step two<br>Step three\n[/flow]"),
    "math":      ("Math fraction",    "[math]§ = a/b[/math]"),
}

# Snippets that wrap the selected text instead of replacing it.
WRAPPERS = {"bold": ("**", "**"), "italic": ("*", "*"),
            "code": ("`", "`"), "link": ("[", "](https://)")}

_TRIGGER = re.compile(r"(?:^|\s)(/\w*)$")
_LIST_LINE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")


class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)

        labels = [f"/{key}   {desc}" for key, (desc, _t) in SNIPPETS.items()]
        self._completer = QCompleter(QStringListModel(labels, self), self)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.activated[str].connect(self._on_completion)

        for seq, key in (("Ctrl+B", "bold"), ("Ctrl+I", "italic"), ("Ctrl+K", "link")):
            sc = QShortcut(QKeySequence(seq), self)
            sc.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc.activated.connect(lambda k=key: self.insert_snippet(k))

    # ---- snippet insertion -------------------------------------------------
    def insert_snippet(self, key):
        """Insert snippet `key` at the cursor (or wrap the selection)."""
        if key not in SNIPPETS:
            return
        cursor = self.textCursor()
        if key in WRAPPERS and cursor.hasSelection():
            before, after = WRAPPERS[key]
            selected = cursor.selectedText()
            cursor.insertText(before + selected + after)
        else:
            text = SNIPPETS[key][1]
            marker = text.index(CURSOR)
            cursor.insertText(text.replace(CURSOR, "", 1))
            cursor.movePosition(QTextCursor.MoveOperation.Left,
                                QTextCursor.MoveMode.MoveAnchor,
                                len(text) - marker - 1)
        self.setTextCursor(cursor)
        self.setFocus()

    def _on_completion(self, label):
        key = label.split()[0].lstrip("/")
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Left,
                            QTextCursor.MoveMode.KeepAnchor,
                            len(self._completer.completionPrefix()))
        cursor.removeSelectedText()          # remove the typed "/xyz"
        self.setTextCursor(cursor)
        self.insert_snippet(key)

    # ---- helpers -----------------------------------------------------------
    def _text_before_cursor(self):
        cursor = self.textCursor()
        return cursor.block().text()[:cursor.positionInBlock()]

    def _update_popup(self):
        match = _TRIGGER.search(self._text_before_cursor())
        popup = self._completer.popup()
        if not match:
            popup.hide()
            return
        self._completer.setCompletionPrefix(match.group(1))
        if self._completer.completionCount() == 0:
            popup.hide()
            return
        popup.setCurrentIndex(self._completer.completionModel().index(0, 0))
        rect = self.cursorRect()
        rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width())
        self._completer.complete(rect)

    def _continue_list(self):
        """Enter inside a list line. Return True if handled."""
        m = _LIST_LINE.match(self._text_before_cursor())
        cursor = self.textCursor()
        if not m or cursor.hasSelection() or cursor.positionInBlock() != len(cursor.block().text()):
            return False
        indent, marker, content = m.groups()
        if not content.strip():                      # empty item -> end the list
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.insertBlock()
        else:
            if marker.endswith("."):
                marker = f"{int(marker[:-1]) + 1}."
            cursor.insertBlock()
            cursor.insertText(f"{indent}{marker} ")
        self.setTextCursor(cursor)
        return True

    # ---- key handling ------------------------------------------------------
    def keyPressEvent(self, event):
        popup = self._completer.popup()
        if popup.isVisible() and event.key() in (
                Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab, Qt.Key.Key_Escape):
            event.ignore()                           # completer handles these
            return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and \
                not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if self._continue_list():
                return

        super().keyPressEvent(event)
        if event.text() or event.key() == Qt.Key.Key_Backspace:
            self._update_popup()
