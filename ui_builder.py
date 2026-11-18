"""PART 2 - Window layout (Member 2).

Builds the 3-panel window: sidebar (notes list + search), editor, live preview.
Used by ResearchApp as a mixin, so every `self.xxx` widget is created here.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QListWidget, QPushButton,
    QLabel, QLineEdit, QSplitter, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWebEngineWidgets import QWebEngineView


class UIBuilderMixin:
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
