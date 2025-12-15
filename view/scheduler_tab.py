from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QStandardPaths
from view.task_widget import TaskWidget
import uuid
import os
import json

class SchedulerTab(QWidget):
    """
    The main widget for the Scheduler tab, containing the quick add bar
    and the list of tasks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = [] # This will hold our task data
        self.init_ui()
        loaded = self.load_tasks()
        if not loaded:
            self.load_sample_tasks()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Quick Add Bar ---
        quick_add_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add a new task and press Enter...")
        self.task_input.returnPressed.connect(self.add_task)
        quick_add_layout.addWidget(self.task_input)

        # --- Task List ---
        self.task_list_widget = QListWidget()
        self.task_list_widget.setSpacing(3)

        # --- Clear Button ---
        self.clear_button = QPushButton("Clear Scheduler")
        self.clear_button.clicked.connect(self.clear_all_tasks)

        main_layout.addLayout(quick_add_layout)
        main_layout.addWidget(self.task_list_widget)
        main_layout.addWidget(self.clear_button)

    def add_task(self):
        title = self.task_input.text().strip()
        if not title:
            return

        new_task_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "status": "pending",
            "priority": "medium", # Default priority
        }
        self.tasks.append(new_task_data)
        self.add_task_widget(new_task_data)

        self.task_input.clear()
        self.save_tasks()

    def load_sample_tasks(self):
        """A helper to show some initial data."""
        self.task_input.setText("Review Chapter 3")
        self.add_task()

    def clear_all_tasks(self):
        """Clears all tasks from the scheduler, with confirmation if tasks are incomplete."""
        if not self.tasks:
            return

        incomplete_tasks = [task for task in self.tasks if task.get("status") == "pending"]

        if incomplete_tasks:
            reply = QMessageBox.question(self, 'Confirm Clear',
                                         "You have incomplete tasks. Are you sure you want to clear the entire list?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                return

        self.tasks.clear()
        self.task_list_widget.clear()
        self.save_tasks()

    # ---------------- Persistence ----------------
    def _tasks_file_path(self):
        base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        # Fallback to home if path is empty
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), ".studymate")
        # Ensure app subdir exists
        app_dir = os.path.join(base_dir, "StudyMate") if "StudyMate" not in base_dir else base_dir
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "scheduler_tasks.json")

    def save_tasks(self):
        try:
            path = self._tasks_file_path()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save tasks: {e}")

    def load_tasks(self):
        try:
            path = self._tasks_file_path()
            if not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return False
            # Normalize and populate
            self.tasks = []
            self.task_list_widget.clear()
            for item in data:
                task = {
                    "id": item.get("id", str(uuid.uuid4())),
                    "title": item.get("title", "Untitled Task"),
                    "status": item.get("status", "pending"),
                    "priority": item.get("priority", "medium"),
                }
                self.tasks.append(task)
                self.add_task_widget(task)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load tasks: {e}")
            return False

    def add_task_widget(self, task_data):
        task_item_widget = TaskWidget(task_data)
        task_item_widget.status_changed.connect(self.on_task_status_changed)
        list_item = QListWidgetItem(self.task_list_widget)
        list_item.setSizeHint(task_item_widget.sizeHint())
        self.task_list_widget.addItem(list_item)
        self.task_list_widget.setItemWidget(list_item, task_item_widget)

    def on_task_status_changed(self, task_id, new_status):
        for task in self.tasks:
            if task.get("id") == task_id:
                task["status"] = new_status
                break
        self.save_tasks()