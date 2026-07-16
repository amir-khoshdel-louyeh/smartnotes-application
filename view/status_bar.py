from PyQt5.QtWidgets import QLabel, QStatusBar


class StatusBar(QStatusBar):
    """Status bar with AI activity and live editor statistics."""

    def __init__(self):
        super().__init__()
        self.setSizeGripEnabled(True)

        self.ai_status_label = QLabel("")
        self.editor_info_label = QLabel()

        self.addWidget(self.ai_status_label, 0)
        self.addPermanentWidget(self.editor_info_label)
        self.showMessage("Ready")
        self.update_editor_info(None)

    def set_ai_status(self, text: str) -> None:
        self.ai_status_label.setText(text or "")

    def update_editor_info(self, editor):
        """Updates labels for line/column, word count and reading time."""
        if not editor:
            self.editor_info_label.setText("")
            return

        cursor = editor.textCursor()
        line_num = cursor.blockNumber() + 1
        col_num = cursor.columnNumber() + 1
        text = editor.toPlainText()
        word_count = len(text.split())
        char_count = len(text)
        selected = len(cursor.selectedText())

        parts = [f"Ln {line_num}, Col {col_num}", f"{word_count} words", f"{char_count} chars"]
        if selected:
            parts.append(f"{selected} selected")
        if word_count:
            parts.append(f"~{max(1, round(word_count / 200))} min read")

        self.editor_info_label.setText("   ·   ".join(parts) + "  ")
