"""Task scheduler with filters, progress and JSON persistence."""

import json
import os
import uuid

from PyQt5.QtCore import QStandardPaths, Qt, QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from view.task_widget import TaskWidget

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class SchedulerTab(QWidget):
    """Quick-add task list persisted as JSON under QStandardPaths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []  # list of task dicts
        self.init_ui()
        loaded = self.load_tasks()
        if not loaded:
            self.load_sample_tasks()
        self._refresh_ui()

    # ------------------------------------------------------------------ UI
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Summary card ---
        summary_card = QFrame()
        summary_card.setObjectName("Card")
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        self.summary_label = QLabel("No tasks yet")
        self.summary_label.setObjectName("CardTitle")
        header_row.addWidget(self.summary_label, 1)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", "all")
        self.filter_combo.addItem("Active", "active")
        self.filter_combo.addItem("Done", "done")
        self.filter_combo.setFixedWidth(88)
        self.filter_combo.setToolTip("Filter tasks")
        self.filter_combo.currentIndexChanged.connect(self._refresh_list)
        header_row.addWidget(self.filter_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Priority", "priority")
        self.sort_combo.addItem("Added", "added")
        self.sort_combo.setFixedWidth(92)
        self.sort_combo.setToolTip("Sort tasks")
        self.sort_combo.currentIndexChanged.connect(self._refresh_list)
        header_row.addWidget(self.sort_combo)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        summary_layout.addLayout(header_row)
        summary_layout.addWidget(self.progress_bar)
        main_layout.addWidget(summary_card)

        # --- Quick add ---
        quick_add_layout = QHBoxLayout()
        quick_add_layout.setSpacing(6)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add a new task and press Enter...")
        self.task_input.returnPressed.connect(self.add_task)
        self.add_button = QPushButton("Add")
        self.add_button.setObjectName("Primary")
        self.add_button.clicked.connect(self.add_task)
        quick_add_layout.addWidget(self.task_input, 1)
        quick_add_layout.addWidget(self.add_button)
        main_layout.addLayout(quick_add_layout)

        # --- Task list ---
        self.task_list_widget = QListWidget()
        self.task_list_widget.setSpacing(3)
        self.task_list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        main_layout.addWidget(self.task_list_widget, 1)

        self.empty_label = QLabel("No tasks yet — add your first task above.")
        self.empty_label.setObjectName("EmptyState")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()
        main_layout.addWidget(self.empty_label, 1)

        # --- Footer ---
        footer = QHBoxLayout()
        footer.setSpacing(6)
        self.clear_completed_button = QPushButton("Clear completed")
        self.clear_completed_button.setObjectName("Ghost")
        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)
        self.clear_button = QPushButton("Clear all")
        self.clear_button.setObjectName("Danger")
        self.clear_button.clicked.connect(self.clear_all_tasks)
        footer.addWidget(self.clear_completed_button)
        footer.addStretch(1)
        footer.addWidget(self.clear_button)
        main_layout.addLayout(footer)

    # ------------------------------------------------------------------ actions
    def add_task(self):
        title = self.task_input.text().strip()
        if not title:
            return
        self.add_task_title(title)
        self.task_input.clear()

    def add_task_title(self, title: str, priority: str = "medium") -> None:
        """Add a task programmatically (also used by the study plan shortcut)."""
        title = (title or "").strip()
        if not title:
            return
        new_task_data = {
            "id": str(uuid.uuid4()),
            "title": title,
            "status": "pending",
            "priority": priority if priority in PRIORITY_ORDER else "medium",
        }
        self.tasks.append(new_task_data)
        self.add_task_widget(new_task_data)
        self.save_tasks()
        self._refresh_ui()

    def load_sample_tasks(self):
        """A helper to show some initial data on first run."""
        self.add_task_title("Review Chapter 3")

    def clear_all_tasks(self):
        """Clears all tasks from the scheduler, with confirmation if tasks are incomplete."""
        if not self.tasks:
            return

        incomplete_tasks = [task for task in self.tasks if task.get("status") == "pending"]
        if incomplete_tasks:
            reply = QMessageBox.question(
                self,
                "Confirm Clear",
                "You have incomplete tasks. Are you sure you want to clear the entire list?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self.tasks.clear()
        self.task_list_widget.clear()
        self.save_tasks()
        self._refresh_ui()

    def clear_completed_tasks(self):
        if not any(task.get("status") == "done" for task in self.tasks):
            return
        self.tasks = [task for task in self.tasks if task.get("status") != "done"]
        self.save_tasks()
        self._refresh_list()
        self._refresh_ui()

    # ------------------------------------------------------------------ list
    def _visible_tasks(self):
        filter_value = self.filter_combo.currentData() if "filter_combo" in self.__dict__ else "all"
        tasks = list(self.tasks)
        if filter_value == "active":
            tasks = [task for task in tasks if task.get("status") != "done"]
        elif filter_value == "done":
            tasks = [task for task in tasks if task.get("status") == "done"]

        sort_value = self.sort_combo.currentData() if "sort_combo" in self.__dict__ else "priority"
        if sort_value == "priority":
            tasks.sort(key=lambda task: PRIORITY_ORDER.get(task.get("priority", "medium"), 1))
        return tasks

    def _refresh_list(self, *_args):
        if "filter_combo" not in self.__dict__:
            return
        self.task_list_widget.clear()
        for task in self._visible_tasks():
            self.add_task_widget(task)
        self._refresh_ui()

    def _refresh_ui(self):
        # Guard also covers partially constructed widgets in unit tests.
        if "progress_bar" not in self.__dict__:
            return

        total = len(self.tasks)
        done = sum(1 for task in self.tasks if task.get("status") == "done")
        pending = total - done

        if total == 0:
            self.summary_label.setText("No tasks yet")
        elif pending == 0:
            self.summary_label.setText("All tasks complete")
        else:
            self.summary_label.setText(f"{pending} to go · {done} done")
        self.progress_bar.setValue(int(round(done / total * 100)) if total else 0)
        self.clear_completed_button.setEnabled(done > 0)
        self.clear_button.setEnabled(total > 0)

        visible = self._visible_tasks()
        self.task_list_widget.setVisible(bool(visible))
        self.empty_label.setVisible(not visible)

        filter_value = self.filter_combo.currentData()
        if total == 0:
            self.empty_label.setText("No tasks yet — add your first task above.")
        elif filter_value == "active":
            self.empty_label.setText("Nothing active. Great work!")
        elif filter_value == "done":
            self.empty_label.setText("No completed tasks yet.")
        else:
            self.empty_label.setText("No tasks to show.")

    def add_task_widget(self, task_data):
        task_item_widget = TaskWidget(task_data)
        task_item_widget.status_changed.connect(self.on_task_status_changed)
        task_item_widget.priority_changed.connect(self.on_task_priority_changed)
        task_item_widget.request_delete.connect(self.on_task_delete)
        task_item_widget.request_edit.connect(self.on_task_edit)
        list_item = QListWidgetItem(self.task_list_widget)
        list_item.setSizeHint(task_item_widget.sizeHint())
        self.task_list_widget.addItem(list_item)
        self.task_list_widget.setItemWidget(list_item, task_item_widget)

    # ------------------------------------------------------------------ signals
    def _schedule_refresh(self):
        # Defer list rebuild until the widget that emitted the signal is done.
        if "filter_combo" in self.__dict__:
            QTimer.singleShot(0, self._refresh_list)

    def on_task_status_changed(self, task_id, new_status):
        for task in self.tasks:
            if task.get("id") == task_id:
                task["status"] = new_status
                break
        self.save_tasks()
        self._refresh_ui()
        self._schedule_refresh()

    def on_task_priority_changed(self, task_id, new_priority):
        for task in self.tasks:
            if task.get("id") == task_id:
                task["priority"] = new_priority
                break
        self.save_tasks()
        self._refresh_ui()
        self._schedule_refresh()

    def on_task_edit(self, task_id, new_title):
        for task in self.tasks:
            if task.get("id") == task_id:
                task["title"] = new_title
                break
        self.save_tasks()

    def on_task_delete(self, task_id):
        self.tasks = [t for t in self.tasks if t.get("id") != task_id]
        for index in range(self.task_list_widget.count()):
            item = self.task_list_widget.item(index)
            widget = self.task_list_widget.itemWidget(item)
            if widget and getattr(widget, "task_data", {}).get("id") == task_id:
                self.task_list_widget.takeItem(index)
                break
        self.save_tasks()
        self._refresh_ui()

    # ------------------------------------------------------------------ persistence
    def _tasks_file_path(self):
        base_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), ".studymate")
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
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return False
            self.tasks = []
            self.task_list_widget.clear()
            for item in data:
                if not isinstance(item, dict):
                    continue
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
