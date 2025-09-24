from PyQt5.QtWidgets import QTextEdit

class EditorArea(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Open a file to start studying...")
