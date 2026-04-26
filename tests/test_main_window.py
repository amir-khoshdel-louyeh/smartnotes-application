import unittest
from unittest.mock import MagicMock, patch

try:
    from PyQt5.QtWidgets import QApplication
    from view.main_window import MainWindow
    PYQT_AVAILABLE = True
except ImportError:
    MainWindow = None
    QApplication = None
    PYQT_AVAILABLE = False


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 is not installed; MainWindow tests are skipped.")
class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        patcher = patch("view.main_window.MainWindow.preload_models", lambda self: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.window = MainWindow()

    def test_close_event_calls_lifecycle_service_and_accepts(self):
        event = MagicMock()
        with patch("view.main_window.LifecycleService.confirm_shutdown", return_value=True) as confirm:
            self.window.closeEvent(event)

        confirm.assert_called_once_with(self.window.file_handler, self.window.settings_manager)
        event.accept.assert_called_once()
        event.ignore.assert_not_called()

    def test_close_event_ignores_when_shutdown_cancelled(self):
        event = MagicMock()
        with patch("view.main_window.LifecycleService.confirm_shutdown", return_value=False) as confirm:
            self.window.closeEvent(event)

        confirm.assert_called_once_with(self.window.file_handler, self.window.settings_manager)
        event.ignore.assert_called_once()
        event.accept.assert_not_called()

    def test_find_next_delegates_to_search_service(self):
        editor = MagicMock()
        self.window.current_editor = MagicMock(return_value=editor)
        self.window.find_input.setText("test")
        self.window.find_case_sensitive_checkbox.isChecked = MagicMock(return_value=False)

        with patch("view.main_window.SearchService.find_next", return_value=True) as find_next:
            self.window.find_next()

        find_next.assert_called_once_with(editor, "test", False)

    def test_replace_all_updates_editor_text_when_matches_found(self):
        editor = MagicMock()
        editor.toPlainText.return_value = "hello hello"
        self.window.current_editor = MagicMock(return_value=editor)
        self.window.find_input.setText("hello")
        self.window.replace_input.setText("hi")
        self.window.find_case_sensitive_checkbox.isChecked = MagicMock(return_value=False)

        with patch("view.main_window.SearchService.replace_all", return_value=("hi hi", 2)) as replace_all:
            self.window.replace_all()

        replace_all.assert_called_once_with("hello hello", "hello", "hi", False)
        editor.setPlainText.assert_called_once_with("hi hi")
        editor.document().setModified.assert_called_once_with(True)
