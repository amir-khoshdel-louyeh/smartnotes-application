from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QFrame, QComboBox, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

class TaskWidget(QWidget):
    """
    A widget representing a single task in the daily planner.
    It includes a priority indicator, a checkbox, and the task title.
    """
    status_changed = pyqtSignal(str, str)  # (task_id, new_status)
    priority_changed = pyqtSignal(str, str)  # (task_id, new_priority)
    request_delete = pyqtSignal(str)  # task_id
    request_edit = pyqtSignal(str, str)  # task_id, new_title

    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self._editing = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)

        # 1. Priority Indicator
        self.priority_indicator = QFrame()
        self.priority_indicator.setFrameShape(QFrame.VLine)
        self.priority_indicator.setFrameShadow(QFrame.Sunken)
        self.priority_indicator.setLineWidth(3)
        self._apply_priority_color()

        # 2. Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data.get("status") == "done")
        self.checkbox.stateChanged.connect(self.on_status_changed)

        # 3. Title Label
        self.title_label = QLabel(self.task_data.get("title", "Untitled Task"))
        self.title_label.setSizePolicy(self.title_label.sizePolicy().horizontalPolicy(), self.title_label.sizePolicy().verticalPolicy())
        self.title_label.mouseDoubleClickEvent = self.start_edit

        # 4. Inline editor (hidden)
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.task_data.get("title", ""))
        self.title_edit.hide()
        self.title_edit.returnPressed.connect(self.finish_edit)
        self.title_edit.editingFinished.connect(self.finish_edit)

        # 5. Priority combo
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "medium", "high"])
        self.priority_combo.setCurrentText(self.task_data.get("priority", "medium"))
        self.priority_combo.setToolTip("Priority")
        self.priority_combo.currentTextChanged.connect(self.on_priority_changed)
        self.priority_combo.setMaximumWidth(90)

        # 6. Delete button
        self.delete_button = QPushButton("✕")
        self.delete_button.setToolTip("Delete task")
        self.delete_button.setMaximumWidth(28)
        self.delete_button.clicked.connect(lambda: self.request_delete.emit(self.task_data.get("id", "")))

        layout.addWidget(self.priority_indicator)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.title_label, 1)  # Stretch factor
        layout.addWidget(self.title_edit, 1)
        layout.addWidget(self.priority_combo)
        layout.addWidget(self.delete_button)

        self.update_style()

    def _apply_priority_color(self):
        priority_color = {
            "high": "#ff4757",
            "medium": "#ffa502",
            "low": "#2ed573"
        }.get(self.task_data.get("priority", "low"), "#7f8fa6")
        self.priority_indicator.setStyleSheet(f"color: {priority_color};")

    def on_status_changed(self, state):
        self.task_data["status"] = "done" if state == Qt.Checked else "pending"
        self.update_style()
        task_id = self.task_data.get("id", "")
        self.status_changed.emit(task_id, self.task_data["status"])

    def on_priority_changed(self, new_priority):
        self.task_data["priority"] = new_priority
        self._apply_priority_color()
        self.priority_changed.emit(self.task_data.get("id", ""), new_priority)

    def start_edit(self, event=None):
        self._editing = True
        self.title_label.hide()
        self.title_edit.setText(self.task_data.get("title", ""))
        self.title_edit.show()
        self.title_edit.selectAll()
        self.title_edit.setFocus()

    def finish_edit(self):
        if not self._editing:
            return
        # avoid double call from returnPressed + editingFinished
        if not self.title_edit.isVisible():
            return
        self._editing = False
        new_title = self.title_edit.text().strip()
        if new_title and new_title != self.task_data.get("title"):
            self.task_data["title"] = new_title
            self.title_label.setText(new_title)
            self.request_edit.emit(self.task_data.get("id", ""), new_title)
        self.title_edit.hide()
        self.title_label.show()

    def update_style(self):
        if self.task_data["status"] == "done":
            font = self.title_label.font()
            font.setStrikeOut(True)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet("color: #888;")
        else:
            font = self.title_label.font()
            font.setStrikeOut(False)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet("")