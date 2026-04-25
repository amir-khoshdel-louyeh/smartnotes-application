import unittest
from unittest.mock import MagicMock

from services.lifecycle import LifecycleService


class TestLifecycleService(unittest.TestCase):
    def test_confirm_shutdown_returns_false_when_close_all_cancelled(self):
        file_handler = MagicMock()
        file_handler.close_all_files.return_value = False
        settings_manager = MagicMock()

        result = LifecycleService.confirm_shutdown(file_handler, settings_manager)

        self.assertFalse(result)
        settings_manager.sync.assert_not_called()

    def test_confirm_shutdown_syncs_when_close_all_succeeds(self):
        file_handler = MagicMock()
        file_handler.close_all_files.return_value = True
        settings_manager = MagicMock()

        result = LifecycleService.confirm_shutdown(file_handler, settings_manager)

        self.assertTrue(result)
        settings_manager.sync.assert_called_once()
