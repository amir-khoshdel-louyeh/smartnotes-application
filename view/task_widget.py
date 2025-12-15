from PyQt5.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal

class TaskWidget(QWidget):
    """
    A widget representing a single task in the daily planner.
    It includes a priority indicator, a checkbox, and the task title.
    """
    status_changed = pyqtSignal(str, str)  # (task_id, new_status)
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 1. Priority Indicator
        self.priority_indicator = QFrame()
        self.priority_indicator.setFrameShape(QFrame.VLine)
        self.priority_indicator.setFrameShadow(QFrame.Sunken)
        self.priority_indicator.setLineWidth(3)
        priority_color = {
            "high": "#ff4757",
            "medium": "#ffa502",
            "low": "#2ed573"
        }.get(self.task_data.get("priority", "low"), "#7f8fa6")
        self.priority_indicator.setStyleSheet(f"color: {priority_color};")

        # 2. Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data.get("status") == "done")
        self.checkbox.stateChanged.connect(self.on_status_changed)

        # 3. Title Label
        self.title_label = QLabel(self.task_data.get("title", "Untitled Task"))
        self.title_label.setSizePolicy(self.title_label.sizePolicy().horizontalPolicy(), self.title_label.sizePolicy().verticalPolicy())

        layout.addWidget(self.priority_indicator)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.title_label, 1) # Stretch factor

        self.update_style()

    def on_status_changed(self, state):
        self.task_data["status"] = "done" if state == Qt.Checked else "pending"
        self.update_style()
        # Emit change so parent can persist tasks
        task_id = self.task_data.get("id", "")
        self.status_changed.emit(task_id, self.task_data["status"])

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
            # Reset stylesheet to use the theme's default color
            self.title_label.setStyleSheet("")