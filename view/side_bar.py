from PyQt5.QtWidgets import QDockWidget, QTabWidget, QWidget, QVBoxLayout, QLabel, QStyle, QPushButton, QComboBox, QTextEdit, QFormLayout, QPlainTextEdit, QFontComboBox, QSpinBox, QCheckBox, QGroupBox, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIcon

class SideBar(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(" ", parent) # Title is removed as tabs have titles
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setMovable(True)

        # Get standard icons
        style = self.style()
        self.settings_icon = QIcon(style.standardPixmap(QStyle.SP_FileDialogDetailedView))
        ai_icon = QIcon(style.standardPixmap(QStyle.SP_ComputerIcon))
        scheduler_icon = QIcon(style.standardPixmap(QStyle.SP_DialogYesButton))

        # Settings Tab
        self.init_settings_tab()

        # AI Tab
        self.init_ai_tab(ai_icon)

        # Scheduler Tab
        self.init_scheduler_tab(scheduler_icon)
        
        self.setWidget(self.tabs)

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
        appearance_layout.addRow("Editor Font:", self.font_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 30)
        appearance_layout.addRow("Font Size:", self.font_size_spinbox)

        self.word_wrap_checkbox = QCheckBox("Enable Word Wrap")
        appearance_layout.addRow(self.word_wrap_checkbox)

        main_layout.addWidget(appearance_group)

        # --- Toggle Button ---
        self.toggle_sidebar_button = QPushButton("Toggle Sidebar")
        main_layout.addWidget(self.toggle_sidebar_button)

        # --- Storage Group ---
        storage_group = QGroupBox("Storage")
        storage_layout = QVBoxLayout(storage_group)

        storage_type_layout = QFormLayout()
        self.storage_type_combo = QComboBox()
        self.storage_type_combo.addItems(["JSON File", "SQLite"])
        self.storage_type_combo.setEnabled(False) # Placeholder
        storage_type_layout.addRow("Note Storage:", self.storage_type_combo)
        storage_layout.addLayout(storage_type_layout)

        backup_restore_layout = QHBoxLayout()
        self.backup_button = QPushButton("Backup")
        self.restore_button = QPushButton("Restore")
        backup_restore_layout.addWidget(self.backup_button)
        backup_restore_layout.addWidget(self.restore_button)
        storage_layout.addLayout(backup_restore_layout)

        default_path_layout = QHBoxLayout()
        self.default_path_edit = QLineEdit()
        self.default_path_edit.setPlaceholderText("Default Import/Export Path...")
        self.default_path_button = QPushButton("Browse")
        default_path_layout.addWidget(self.default_path_edit)
        default_path_layout.addWidget(self.default_path_button)
        storage_layout.addLayout(default_path_layout)

        main_layout.addWidget(storage_group)

        main_layout.addStretch() # Pushes everything to the top
        self.tabs.addTab(self.settings_tab, self.settings_icon, "Settings")

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

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("Summary will appear here...")
        layout.addWidget(self.summary_output)

        self.ai_tab.setLayout(layout)
        self.tabs.addTab(self.ai_tab, icon, "AI")

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
        self.tabs.addTab(self.scheduler_tab, icon, "Scheduler")
