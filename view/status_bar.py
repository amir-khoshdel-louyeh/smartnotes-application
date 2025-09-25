from PyQt5.QtWidgets import QStatusBar, QLabel

class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.editor_info_label = QLabel()
        
        self.addPermanentWidget(self.editor_info_label)
        self.showMessage("Ready")
        self.update_editor_info(None)

    def update_editor_info(self, editor):
        """Updates labels for word count, line/col number, etc."""
        if not editor:
            self.editor_info_label.setText("")
            return

        cursor = editor.textCursor()
        line_num = cursor.blockNumber() + 1
        col_num = cursor.columnNumber() + 1
        word_count = len(editor.toPlainText().split())
        self.editor_info_label.setText(f"  Ln {line_num}, Col {col_num}   |   Words: {word_count}  ")
