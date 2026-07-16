"""Main application toolbar built from shared menu actions."""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QSizePolicy, QToolBar, QWidget


class MainToolBar(QToolBar):
    """Compact, text-first toolbar with the most used actions."""

    def __init__(self, actions: dict, parent=None):
        super().__init__("Main", parent)
        self.setObjectName("MainToolBar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)

        for key in ("new", "open", "save"):
            if key in actions:
                self.addAction(actions[key])
        self.addSeparator()
        for key in ("summarize", "key_points", "mind_map"):
            if key in actions:
                self.addAction(actions[key])
        self.addSeparator()
        if "replace" in actions:
            self.addAction(actions["replace"])

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        if "preview" in actions:
            self.addAction(actions["preview"])
        if "dark_mode" in actions:
            self.addAction(actions["dark_mode"])
