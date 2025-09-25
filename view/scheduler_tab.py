from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from view.task_widget import TaskWidget
import uuid

class SchedulerTab(QWidget):
    """
    The main widget for the Scheduler tab, containing the quick add bar
    and the list of tasks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = [] # This will hold our task data
        self.init_ui()
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

        task_item_widget = TaskWidget(new_task_data)
        list_item = QListWidgetItem(self.task_list_widget)
        list_item.setSizeHint(task_item_widget.sizeHint())
        self.task_list_widget.addItem(list_item)
        self.task_list_widget.setItemWidget(list_item, task_item_widget)

        self.task_input.clear()

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