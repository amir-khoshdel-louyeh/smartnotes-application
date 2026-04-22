from view.file_handler import FileHandler
from view.file_service import FileService


class UIController:
    """Coordinates UI components with service layers."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.file_service = FileService()
        self.file_handler = FileHandler(main_window, self.file_service)
