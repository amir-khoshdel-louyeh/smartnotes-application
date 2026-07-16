import os

from PyQt5.QtCore import pyqtSignal

from view.code_editor import CodeEditor


class EditorArea(CodeEditor):
    """Code editor tab that accepts dropped files."""

    file_dropped = pyqtSignal(str)

    def __init__(self, file_path=None, parent=None):
        super().__init__(file_path=file_path, parent=parent)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        local_files = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and os.path.isfile(url.toLocalFile())
        ]
        if local_files:
            event.acceptProposedAction()
            for path in local_files:
                self.file_dropped.emit(path)
            return
        super().dropEvent(event)
