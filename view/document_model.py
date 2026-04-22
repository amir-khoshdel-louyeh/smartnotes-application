import os


class DocumentModel:
    """Tracks metadata and state for an open document."""

    def __init__(self, file_path: str | None = None, is_temporary: bool = False, is_pdf: bool = False):
        self.file_path = file_path
        self.is_temporary = is_temporary
        self.is_pdf = is_pdf

    @property
    def display_name(self) -> str:
        return os.path.basename(self.file_path) if self.file_path else "Untitled"

    def update_path(self, new_path: str) -> None:
        self.file_path = new_path

    def mark_temporary(self, value: bool = True) -> None:
        self.is_temporary = value
