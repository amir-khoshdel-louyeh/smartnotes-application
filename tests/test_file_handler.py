import unittest
from unittest.mock import MagicMock

try:
    from view.file_handler import FileHandler
    FILE_HANDLER_AVAILABLE = True
except ImportError:
    FileHandler = None
    FILE_HANDLER_AVAILABLE = False


class DummyTabWidget:
    def __init__(self, editors):
        self._editors = editors
        self.current_index = None

    def count(self):
        return len(self._editors)

    def widget(self, index):
        return self._editors[index]

    def setCurrentIndex(self, index):
        self.current_index = index


class DummyMainWindow:
    def __init__(self, tab_widget):
        self.tab_widget = tab_widget
        self.status_bar = MagicMock()
        self.sidebar = MagicMock()
        self.settings_model = MagicMock()
        self.update_window_title = MagicMock()
        self.update_status_bar = MagicMock()
        self.on_modification_changed = MagicMock()


class DummyEditor:
    def __init__(self, file_path):
        self.file_path = file_path


@unittest.skipUnless(FILE_HANDLER_AVAILABLE, "PyQt5 is not installed; FileHandler tests are skipped.")
class TestFileHandler(unittest.TestCase):
    def test_is_file_open_returns_true_when_editor_already_open(self):
        dummy_editor = DummyEditor("/tmp/test.txt")
        dummy_tab = DummyTabWidget([dummy_editor])
        main_window = DummyMainWindow(dummy_tab)
        handler = FileHandler(main_window, file_service=MagicMock())

        self.assertTrue(handler.is_file_open("/tmp/test.txt"))
        self.assertEqual(dummy_tab.current_index, 0)

    def test_is_file_open_returns_false_when_no_editor_matches(self):
        dummy_editor = DummyEditor("/tmp/other.txt")
        dummy_tab = DummyTabWidget([dummy_editor])
        main_window = DummyMainWindow(dummy_tab)
        handler = FileHandler(main_window, file_service=MagicMock())

        self.assertFalse(handler.is_file_open("/tmp/test.txt"))
        self.assertIsNone(dummy_tab.current_index)
