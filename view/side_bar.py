from PyQt5.QtWidgets import QDockWidget, QTabWidget, QWidget, QVBoxLayout, QLabel, QStyle, QPushButton, QComboBox, QTextEdit, QFormLayout, QFontComboBox, QSpinBox, QCheckBox, QGroupBox, QHBoxLayout, QLineEdit, QTreeView, QFileSystemModel, QSizePolicy, QStackedWidget, QFileDialog, QToolBar, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDir, pyqtSignal
from view.scheduler_tab import SchedulerTab
import os

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
        self.scheduler_tab = SchedulerTab(self)

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
        # Use a QVBoxLayout to hold the stacked widget
        explore_tab_layout = QVBoxLayout(self.explore_tab)
        explore_tab_layout.setContentsMargins(5, 5, 5, 5)
        explore_tab_layout.setSpacing(0)

        # --- Stacked Widget for switching between welcome and file view ---
        self.explore_stack = QStackedWidget()
        explore_tab_layout.addWidget(self.explore_stack)

        # --- 1. Welcome Screen Widget ---
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignCenter)

        welcome_label = QLabel("File Explorer")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 10px;")

        self.open_folder_button = QPushButton(self.style().standardIcon(QStyle.SP_DirOpenIcon), " Open Folder")
        self.open_file_button = QPushButton(self.style().standardIcon(QStyle.SP_FileIcon), " Open File")
        self.new_file_button = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), " New File")

        welcome_layout.addWidget(QLabel("You have not yet opened a folder."))
        welcome_layout.addWidget(self.open_folder_button)
        welcome_layout.addWidget(self.open_file_button)
        welcome_layout.addWidget(self.new_file_button)
        welcome_layout.addStretch()

        # --- 2. File Explorer View (initially just a container) ---
        self.explore_view_widget = QWidget()
        tree_layout = QVBoxLayout(self.explore_view_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)

        # Toolbar for file explorer
        toolbar = QToolBar()
        toolbar.setIconSize(self.style().standardIcon(QStyle.SP_DirOpenIcon).actualSize(self.sizeHint() / 2)) # Smaller icons
        self.new_file_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "New File", self)
        self.new_folder_action = QAction(self.style().standardIcon(QStyle.SP_DirIcon), "New Folder", self)
        self.refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        self.collapse_action = QAction(self.style().standardIcon(QStyle.SP_ArrowUp), "Collapse All", self)
        toolbar.addAction(self.new_file_action)
        toolbar.addAction(self.new_folder_action)
        toolbar.addAction(self.refresh_action)
        toolbar.addAction(self.collapse_action)
        tree_layout.addWidget(toolbar)

        # File System Model and Tree View
        self.file_model = QFileSystemModel()
        self.explore_view = QTreeView()
        self.explore_view.setModel(self.file_model)
        self.explore_view.setHeaderHidden(True)
        self.explore_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.explore_view.hideColumn(1)  # Size
        self.explore_view.hideColumn(2)  # Type
        self.explore_view.hideColumn(3)  # Date Modified
        self.explore_view.setIndentation(15)
        self.explore_view.setSortingEnabled(True)
        tree_layout.addWidget(self.explore_view)

        self.explore_stack.addWidget(welcome_widget)
        self.explore_stack.addWidget(self.explore_view_widget)

    def open_folder_in_explorer(self):
        """Opens a directory dialog and sets the file explorer root."""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", QDir.homePath())
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.explore_view.setRootIndex(self.file_model.index(folder_path))
            self.explore_stack.setCurrentWidget(self.explore_view_widget)
            self.add_actions_to_explorer_view()

    def add_actions_to_explorer_view(self):
        """Moves the action buttons to the bottom of the explorer view."""
        if self.open_folder_button.parent() != self.explore_view_widget:
            explorer_layout = self.explore_view_widget.layout()
            explorer_layout.addStretch()
            explorer_layout.addWidget(self.open_folder_button)
            explorer_layout.addWidget(self.open_file_button)
            explorer_layout.addWidget(self.new_file_button)


    def show_directory_in_explorer(self, path):
        """Sets the file explorer root to the directory of the given path."""
        if not path:
            return
        folder_path = os.path.dirname(path) if os.path.isfile(path) else path
        self.file_model.setRootPath(folder_path)
        self.explore_view.setRootIndex(self.file_model.index(folder_path))
        self.explore_stack.setCurrentWidget(self.explore_view_widget)
        self.add_actions_to_explorer_view()

    def create_new_folder(self):
        """Creates a new folder in the currently selected directory."""
        index = self.explore_view.currentIndex()
        if not index.isValid():
            # If nothing is selected, use the root path
            dir_path = self.file_model.rootPath()
        else:
            dir_path = self.file_model.filePath(index)
            if not self.file_model.isDir(index):
                dir_path = self.file_model.filePath(index.parent())
        self.file_model.mkdir(self.file_model.index(dir_path), "New Folder")

    def refresh_explorer(self):
        self.file_model.setRootPath(self.file_model.rootPath()) # Re-reading the root path refreshes it

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
