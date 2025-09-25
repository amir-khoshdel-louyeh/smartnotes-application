from PyQt5.QtWidgets import QDockWidget, QTabWidget, QWidget, QVBoxLayout, QLabel, QStyle, QPushButton, QComboBox, QTextEdit, QFormLayout, QPlainTextEdit, QFontComboBox, QSpinBox, QCheckBox, QGroupBox, QHBoxLayout, QLineEdit, QTreeView, QFileSystemModel, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDir, pyqtSignal

class SideBar(QDockWidget):
    resized = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(" ", parent)  # Title is removed as tabs have titles
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setMovable(True)

        # Get standard icons
        style = self.style()
        self.settings_icon = QIcon(style.standardPixmap(QStyle.SP_FileDialogDetailedView))
        ai_icon = QIcon(style.standardPixmap(QStyle.SP_ComputerIcon))
        scheduler_icon = QIcon(style.standardPixmap(QStyle.SP_DialogYesButton))
        explore_icon = QIcon(style.standardPixmap(QStyle.SP_DirIcon))

        # Initialize all tabs first
        self.init_explore_tab()
        # AI Tab
        self.init_ai_tab(ai_icon)
        # Settings Tab
        self.init_settings_tab()
        # Scheduler Tab
        self.init_scheduler_tab(scheduler_icon)

        # Now add all initialized tabs to the QTabWidget in the desired order
        self.tabs.addTab(self.explore_tab, explore_icon, "Explore")
        self.tabs.addTab(self.ai_tab, ai_icon, "AI")
        self.tabs.addTab(self.scheduler_tab, scheduler_icon, "Scheduler")
        self.tabs.addTab(self.settings_tab, self.settings_icon, "Settings")

        self.setWidget(self.tabs)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Emit the new width, but only when it's not collapsed to avoid spamming signals
        # during collapse/expand animations.
        if event.size().width() > 50 and event.oldSize().width() > 50:
            self.resized.emit(event.size().width())

    def init_explore_tab(self):
        self.explore_tab = QWidget()
        layout = QVBoxLayout(self.explore_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.homePath())
        self.explore_view = QTreeView()
        self.explore_view.setModel(self.file_model)
        self.explore_view.setRootIndex(self.file_model.index(QDir.homePath()))
        self.explore_view.setHeaderHidden(True)

        # Hide columns for size, type, and date modified to only show the file/directory names
        self.explore_view.hideColumn(1)  # Size
        self.explore_view.hideColumn(2)  # Type
        self.explore_view.hideColumn(3)  # Date Modified
        layout.addWidget(self.explore_view)

    def init_settings_tab(self):
        self.settings_tab = QWidget()
        main_layout = QVBoxLayout(self.settings_tab)

        # --- Appearance Group ---
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        appearance_layout.addRow("Theme:", self.theme_combo)

        self.font_combo = QFontComboBox()
        # Set size policy to allow the font combo box to be shrunk, preventing it from
        # enforcing a large minimum width on the sidebar.
        font_policy = self.font_combo.sizePolicy()
        font_policy.setHorizontalPolicy(QSizePolicy.Ignored)
        self.font_combo.setSizePolicy(font_policy)
        appearance_layout.addRow("Editor Font:", self.font_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 30)
        appearance_layout.addRow("Font Size:", self.font_size_spinbox)

        # --- Sidebar Width Control ---
        sidebar_width_widget = QWidget()
        sidebar_width_layout = QHBoxLayout(sidebar_width_widget)
        sidebar_width_layout.setContentsMargins(0,0,0,0)
        self.sidebar_width_decrease_button = QPushButton("-")
        self.sidebar_width_label = QLabel("300")
        self.sidebar_width_increase_button = QPushButton("+")
        sidebar_width_layout.addWidget(self.sidebar_width_decrease_button)
        sidebar_width_layout.addWidget(self.sidebar_width_label, 1, Qt.AlignCenter)
        sidebar_width_layout.addWidget(self.sidebar_width_increase_button)
        appearance_layout.addRow("Sidebar Width:", sidebar_width_widget)

        # --- Sidebar Font Size Control ---
        sidebar_font_widget = QWidget()
        sidebar_font_layout = QHBoxLayout(sidebar_font_widget)
        sidebar_font_layout.setContentsMargins(0,0,0,0)
        self.sidebar_font_size_decrease_button = QPushButton("-")
        self.sidebar_font_size_label = QLabel("10")
        self.sidebar_font_size_increase_button = QPushButton("+")
        sidebar_font_layout.addWidget(self.sidebar_font_size_decrease_button)
        sidebar_font_layout.addWidget(self.sidebar_font_size_label, 1, Qt.AlignCenter)
        sidebar_font_layout.addWidget(self.sidebar_font_size_increase_button)
        appearance_layout.addRow("Sidebar Font Size:", sidebar_font_widget)

        self.word_wrap_checkbox = QCheckBox("Enable Word Wrap")
        appearance_layout.addRow(self.word_wrap_checkbox)

        main_layout.addWidget(appearance_group)

        main_layout.addStretch()  # Pushes everything to the top
    # Keep old theme_button for compatibility with existing signal connections
    @property
    def theme_button(self):
        return self.theme_combo

    def init_ai_tab(self, icon):
        self.ai_tab = QWidget()
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.summary_length_combo = QComboBox()
        self.summary_length_combo.addItems(["Short", "Medium", "Long"])
        self.summary_length_combo.setCurrentText("Medium")
        form_layout.addRow("Summary Length:", self.summary_length_combo)
        layout.addLayout(form_layout)

        self.summarize_button = QPushButton("Summarize")
        layout.addWidget(self.summarize_button)

        self.key_points_button = QPushButton("Get Key Points")
        layout.addWidget(self.key_points_button)

        # --- External AI Tools ---
        external_ai_group = QGroupBox("Launch External AI")
        external_ai_layout = QHBoxLayout(external_ai_group)

        self.gemini_button = QPushButton("Gemini")
        self.chatgpt_button = QPushButton("ChatGPT")
        self.copilot_button = QPushButton("Copilot")
        external_ai_layout.addWidget(self.gemini_button)
        external_ai_layout.addWidget(self.chatgpt_button)
        external_ai_layout.addWidget(self.copilot_button)
        layout.addWidget(external_ai_group)

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("Summary will appear here...")
        layout.addWidget(self.summary_output)
        self.ai_tab.setLayout(layout)

    def init_scheduler_tab(self, icon):
        self.scheduler_tab = QWidget()
        layout = QVBoxLayout()
        
        # --- Study Plan Group ---
        study_plan_group = QGroupBox("Study Plan")
        study_plan_layout = QVBoxLayout(study_plan_group)
        self.suggest_schedule_button = QPushButton("Suggest Study Plan")
        study_plan_layout.addWidget(self.suggest_schedule_button)
        self.schedule_output = QPlainTextEdit()
        self.schedule_output.setReadOnly(True)
        self.schedule_output.setPlaceholderText("Your personalized study plan will appear here...")
        study_plan_layout.addWidget(self.schedule_output)
        
        # -- Toggle Sidebar Button --
        self.toggle_sidebar_button_scheduler = QPushButton("Toggle Sidebar")
        study_plan_layout.addWidget(self.toggle_sidebar_button_scheduler)
        layout.addWidget(study_plan_group)

        # --- Reminders Group ---
        reminders_group = QGroupBox("Reminders")
        reminders_layout = QFormLayout(reminders_group)
        self.reminders_checkbox = QCheckBox("Enable Reminders")
        self.reminder_freq_combo = QComboBox()
        self.reminder_freq_combo.addItems(["Daily", "Weekly"])
        reminders_layout.addRow(self.reminders_checkbox)
        reminders_layout.addRow("Frequency:", self.reminder_freq_combo)
        layout.addWidget(reminders_group)
        
        layout.addStretch()
        self.scheduler_tab.setLayout(layout)
