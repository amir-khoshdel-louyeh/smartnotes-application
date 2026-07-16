from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

PRIORITY_COLORS = {
    "high": "#ff5c6c",
    "medium": "#ffb020",
    "low": "#34c77b",
}

PRIORITY_LABELS = [("High", "high"), ("Medium", "medium"), ("Low", "low")]


class TaskWidget(QWidget):
    """A single task row: priority bar, checkbox, editable title, priority, delete."""

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
        layout.setContentsMargins(10, 7, 8, 7)
        layout.setSpacing(8)

        # 1. Priority indicator
        self.priority_indicator = QFrame()
        self.priority_indicator.setFixedWidth(4)
        self.priority_indicator.setMinimumHeight(18)
        self.priority_indicator.setStyleSheet(
            f"background-color: {self._priority_color()}; border-radius: 2px;"
        )

        # 2. Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data.get("status") == "done")
        self.checkbox.setToolTip("Mark as done")
        self.checkbox.stateChanged.connect(self.on_status_changed)

        # 3. Title label
        title = self.task_data.get("title", "Untitled Task")
        self.title_label = QLabel(title)
        self.title_label.setToolTip(title)
        self.title_label.setWordWrap(False)
        self.title_label.mouseDoubleClickEvent = self.start_edit

        # 4. Inline editor (hidden)
        self.title_edit = QLineEdit()
        self.title_edit.setText(self.task_data.get("title", ""))
        self.title_edit.hide()
        self.title_edit.returnPressed.connect(self.finish_edit)
        self.title_edit.editingFinished.connect(self.finish_edit)

        # 5. Priority combo (display label, stored value)
        self.priority_combo = QComboBox()
        for label, value in PRIORITY_LABELS:
            self.priority_combo.addItem(label, value)
        current = self.task_data.get("priority", "medium")
        index = self.priority_combo.findData(current)
        self.priority_combo.setCurrentIndex(index if index >= 0 else 1)
        self.priority_combo.setToolTip("Priority")
        self.priority_combo.setFixedWidth(92)
        self.priority_combo.currentIndexChanged.connect(self.on_priority_changed)

        # 6. Delete button
        self.delete_button = QPushButton("✕")
        self.delete_button.setObjectName("IconButton")
        self.delete_button.setToolTip("Delete task")
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.clicked.connect(
            lambda: self.request_delete.emit(self.task_data.get("id", ""))
        )

        layout.addWidget(self.priority_indicator)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.title_label, 1)
        layout.addWidget(self.title_edit, 1)
        layout.addWidget(self.priority_combo)
        layout.addWidget(self.delete_button)

        self.update_style()

    def _priority_color(self) -> str:
        return PRIORITY_COLORS.get(self.task_data.get("priority", "medium"), PRIORITY_COLORS["medium"])

    def _apply_priority_color(self):
        self.priority_indicator.setStyleSheet(
            f"background-color: {self._priority_color()}; border-radius: 2px;"
        )

    def on_status_changed(self, state):
        self.task_data["status"] = "done" if state == Qt.Checked else "pending"
        self.update_style()
        task_id = self.task_data.get("id", "")
        self.status_changed.emit(task_id, self.task_data["status"])

    def on_priority_changed(self, _index):
        new_priority = self.priority_combo.currentData()
        if not new_priority:
            return
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
            self.title_label.setToolTip(new_title)
            self.request_edit.emit(self.task_data.get("id", ""), new_title)
        self.title_edit.hide()
        self.title_label.show()

    def update_style(self):
        font = self.title_label.font()
        if self.task_data.get("status") == "done":
            font.setStrikeOut(True)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet("color: #8b95a5;")
        else:
            font.setStrikeOut(False)
            self.title_label.setFont(font)
            self.title_label.setStyleSheet("")
