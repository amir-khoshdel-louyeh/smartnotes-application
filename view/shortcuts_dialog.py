"""Keyboard shortcut reference dialog."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

SHORTCUTS = [
    (
        "Files",
        [
            ("New file", QKeySequence.New),
            ("Open file", QKeySequence.Open),
            ("Save", QKeySequence.Save),
            ("Save as", QKeySequence.SaveAs),
            ("Close tab", QKeySequence("Ctrl+W")),
            ("Print", QKeySequence.Print),
        ],
    ),
    (
        "Editing",
        [
            ("Find / replace", QKeySequence.Find),
            ("Undo", QKeySequence.Undo),
            ("Redo", QKeySequence("Ctrl+Y")),
            ("Select all", QKeySequence.SelectAll),
        ],
    ),
    (
        "AI tools",
        [
            ("Summarize selection or note", QKeySequence("Ctrl+Alt+S")),
            ("Extract key points", QKeySequence("Ctrl+Alt+K")),
            ("Generate mind map", QKeySequence("Ctrl+Alt+M")),
        ],
    ),
    (
        "View",
        [
            ("Zoom in", QKeySequence("Ctrl++")),
            ("Zoom out", QKeySequence("Ctrl+-")),
            ("Reset zoom", QKeySequence("Ctrl+0")),
            ("Toggle sidebar", QKeySequence("Ctrl+M")),
            ("Toggle markdown preview", QKeySequence("Ctrl+Shift+M")),
            ("Full screen", QKeySequence("F11")),
        ],
    ),
]


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(520, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(14)

        title = QLabel("Keyboard shortcuts")
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        subtitle = QLabel("Work faster without leaving the keyboard.")
        subtitle.setObjectName("Hint")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 6, 0)
        body_layout.setSpacing(12)

        for section_title, entries in SHORTCUTS:
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(8)

            heading = QLabel(section_title)
            heading.setObjectName("CardTitle")
            card_layout.addWidget(heading)

            grid = QGridLayout()
            grid.setHorizontalSpacing(18)
            grid.setVerticalSpacing(7)
            for row, (name, sequence) in enumerate(entries):
                label = QLabel(name)
                keys = QLabel(sequence.toString(QKeySequence.NativeText))
                keys.setObjectName("Pill")
                keys.setAlignment(Qt.AlignCenter)
                grid.addWidget(label, row, 0)
                grid.addWidget(keys, row, 1, Qt.AlignRight)
            grid.setColumnStretch(0, 1)
            card_layout.addLayout(grid)
            body_layout.addWidget(card)

        body_layout.addStretch()
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        close_button = QPushButton("Close")
        close_button.setObjectName("Primary")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)
