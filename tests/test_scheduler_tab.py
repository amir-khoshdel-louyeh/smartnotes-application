import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import json

from view.scheduler_tab import SchedulerTab


class TestSchedulerTab(unittest.TestCase):
    def setUp(self):
        self.qs_patch = patch("view.scheduler_tab.QStandardPaths.writableLocation", return_value="")
        self.qs_patch.start()
        self.msg_patch = patch("view.scheduler_tab.QMessageBox")
        self.msg_patch.start()
        self.expand_patch = patch("view.scheduler_tab.os.path.expanduser", return_value="/tmp")
        self.expand_patch.start()

        self.tab = SchedulerTab.__new__(SchedulerTab)
        self.tab.tasks = []
        self.tab.task_list_widget = MagicMock()
        self.tab.task_input = MagicMock()
        self.tab.task_input.text.return_value = "Test task"
        self.tab.task_input.clear = MagicMock()
        self.tab.add_task_widget = MagicMock()
        self.tab.save_tasks = MagicMock()

    def tearDown(self):
        self.qs_patch.stop()
        self.msg_patch.stop()
        self.expand_patch.stop()

    def test_add_task_creates_pending(self):
        self.tab.add_task()
        self.assertEqual(len(self.tab.tasks), 1)
        self.assertEqual(self.tab.tasks[0]["title"], "Test task")
        self.assertEqual(self.tab.tasks[0]["status"], "pending")
        self.tab.save_tasks.assert_called_once()

    def test_add_task_empty_ignored(self):
        self.tab.task_input.text.return_value = "   "
        self.tab.add_task()
        self.assertEqual(len(self.tab.tasks), 0)

    def test_on_status_changed_updates_and_saves(self):
        self.tab.tasks = [{"id": "123", "title": "t", "status": "pending", "priority": "medium"}]
        self.tab.save_tasks = MagicMock()
        self.tab.on_task_status_changed("123", "done")
        self.assertEqual(self.tab.tasks[0]["status"], "done")
        self.tab.save_tasks.assert_called_once()

    def test_clear_all_with_no_tasks(self):
        self.tab.tasks = []
        self.tab.task_list_widget.clear = MagicMock()
        self.tab.clear_all_tasks()
        self.tab.task_list_widget.clear.assert_not_called()

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            real_tab = SchedulerTab.__new__(SchedulerTab)
            real_tab.tasks = [{"id": "a1", "title": "hello", "status": "pending", "priority": "low"}]
            real_tab.task_list_widget = MagicMock()
            real_tab.task_list_widget.clear = MagicMock()
            path = os.path.join(td, "scheduler_tasks.json")
            with patch.object(real_tab, "_tasks_file_path", return_value=path):
                real_tab.save_tasks = SchedulerTab.save_tasks.__get__(real_tab, SchedulerTab)
                real_tab.load_tasks = SchedulerTab.load_tasks.__get__(real_tab, SchedulerTab)
                real_tab.add_task_widget = MagicMock()
                real_tab.save_tasks()
                self.assertTrue(os.path.exists(path))
                with open(path) as f:
                    data = json.load(f)
                self.assertEqual(data[0]["title"], "hello")
                real_tab.tasks = []
                real_tab.load_tasks()
                self.assertEqual(len(real_tab.tasks), 1)
                self.assertEqual(real_tab.tasks[0]["title"], "hello")
