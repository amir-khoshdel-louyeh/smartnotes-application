from PyQt5.QtWidgets import QTextEdit

class EditorArea(QTextEdit):
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        if not self.file_path:
            self.setPlaceholderText("Create or open a file to start studying...")
        else:
            self.setPlaceholderText("")
