"""StudyMate sidebar: explorer, AI tools, tasks and settings."""

import os

from PyQt5.QtCore import QDir, QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFileSystemModel,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from view.scheduler_tab import SchedulerTab

TEXT_FILTERS = [
    "*.txt",
    "*.md",
    "*.markdown",
    "*.py",
    "*.pdf",
    "*.docx",
    "*.odt",
    "*.json",
    "*.png",
    "*.jpg",
    "*.jpeg",
]


class SideBar(QDockWidget):
    """Dockable workspace sidebar with a custom header and card-based pages."""

    resized = pyqtSignal(int)
    collapse_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("StudyMate", parent)
        self.setObjectName("SideBar")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.setMinimumWidth(240)
        # The custom header replaces the native (empty) dock title bar.
        self.setTitleBarWidget(QWidget(self))

        self._build_tabs()

        container = QWidget()
        container.setObjectName("SidebarContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self.tabs, 1)
        layout.addWidget(self._build_footer())
        self.setWidget(container)

    # ------------------------------------------------------------------ chrome
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("SidebarHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 12, 10, 12)
        layout.setSpacing(8)

        text_column = QVBoxLayout()
        text_column.setSpacing(1)
        title = QLabel("StudyMate")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Local AI study workspace")
        subtitle.setObjectName("AppSubtitle")
        text_column.addWidget(title)
        text_column.addWidget(subtitle)

        self.collapse_button = QPushButton("‹")
        self.collapse_button.setObjectName("IconButton")
        self.collapse_button.setFixedSize(26, 26)
        self.collapse_button.setToolTip("Hide sidebar (Ctrl+M)")
        self.collapse_button.clicked.connect(self.collapse_requested.emit)

        layout.addLayout(text_column, 1)
        layout.addWidget(self.collapse_button, 0, Qt.AlignTop)
        return header

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(14, 7, 14, 7)
        hint = QLabel("v0.3.0 · offline-first")
        hint.setObjectName("Hint")
        layout.addWidget(hint)
        layout.addStretch()
        self.footer_tab_label = QLabel("")
        self.footer_tab_label.setObjectName("Hint")
        layout.addWidget(self.footer_tab_label)
        return footer

    def _build_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SidebarTabs")
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(False)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.init_explore_tab()
        self.init_ai_tab()
        self.scheduler_tab = SchedulerTab(self)
        self.init_settings_tab()

        self.tabs.addTab(self.explore_tab, "Explore")
        self.tabs.addTab(self.ai_tab, "AI")
        self.tabs.addTab(self.scheduler_tab, "Tasks")
        self.tabs.addTab(self.settings_tab, "Settings")

    def _on_tab_changed(self, index: int) -> None:
        if hasattr(self, "footer_tab_label"):
            self.footer_tab_label.setText(self.tabs.tabText(index))

    # ------------------------------------------------------------------ helpers
    def _card(self, title: str, subtitle: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        if title:
            heading = QLabel(title)
            heading.setObjectName("CardTitle")
            layout.addWidget(heading)
        if subtitle:
            hint = QLabel(subtitle)
            hint.setObjectName("Hint")
            hint.setWordWrap(True)
            layout.addWidget(hint)
        return card, layout

    def _scroll_page(self) -> tuple[QScrollArea, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        scroll.setWidget(page)
        return scroll, layout

    def _stepper(self, initial: str) -> tuple[QWidget, QPushButton, QLabel, QPushButton]:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        minus = QPushButton("−")
        minus.setObjectName("IconButton")
        minus.setFixedWidth(26)
        value = QLabel(initial)
        value.setAlignment(Qt.AlignCenter)
        value.setMinimumWidth(34)
        plus = QPushButton("+")
        plus.setObjectName("IconButton")
        plus.setFixedWidth(26)

        layout.addWidget(minus)
        layout.addWidget(value, 1)
        layout.addWidget(plus)
        return widget, minus, value, plus

    # ------------------------------------------------------------------ explore
    def init_explore_tab(self) -> None:
        self.explore_tab = QWidget()
        layout = QVBoxLayout(self.explore_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.explore_stack = QStackedWidget()
        layout.addWidget(self.explore_stack)

        # --- Welcome page -------------------------------------------------
        welcome = QWidget()
        welcome_layout = QVBoxLayout(welcome)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(12)

        welcome_card, welcome_card_layout = self._card(
            "Start exploring",
            "Open a folder to browse your notes, or create a new file to begin.",
        )
        self.open_folder_button = QPushButton("Open folder")
        self.open_folder_button.setObjectName("Primary")
        self.open_file_button = QPushButton("Open file")
        self.new_file_button = QPushButton("New file")
        welcome_card_layout.addWidget(self.open_folder_button)
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(8)
        secondary_row.addWidget(self.open_file_button)
        secondary_row.addWidget(self.new_file_button)
        welcome_card_layout.addLayout(secondary_row)

        tip = QLabel("Tip: drag files onto the window to open them instantly.")
        tip.setObjectName("Hint")
        tip.setWordWrap(True)
        welcome_card_layout.addWidget(tip)

        welcome_layout.addWidget(welcome_card)
        welcome_layout.addStretch(1)

        # --- Explorer page ------------------------------------------------
        self.explore_view_widget = QWidget()
        tree_layout = QVBoxLayout(self.explore_view_widget)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(8)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        style = self.style()
        self.open_folder_action = QAction(style.standardIcon(QStyle.SP_DirOpenIcon), "Open folder", self)
        self.open_folder_action.setToolTip("Open a folder in the explorer")
        self.new_file_action = QAction(style.standardIcon(QStyle.SP_FileIcon), "New file", self)
        self.new_file_action.setToolTip("Create a new file")
        self.new_folder_action = QAction(style.standardIcon(QStyle.SP_FileDialogNewFolder), "New folder", self)
        self.new_folder_action.setToolTip("Create a new folder")
        self.refresh_action = QAction(style.standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        self.refresh_action.setToolTip("Refresh explorer")
        self.collapse_action = QAction(style.standardIcon(QStyle.SP_ArrowUp), "Collapse all", self)
        self.collapse_action.setToolTip("Collapse all folders")
        for action in (
            self.open_folder_action,
            self.new_file_action,
            self.new_folder_action,
        ):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addAction(self.refresh_action)
        toolbar.addAction(self.collapse_action)
        self.open_folder_action.triggered.connect(self.open_folder_in_explorer)
        tree_layout.addWidget(toolbar)

        self.file_model = QFileSystemModel()
        self.file_model.setNameFilters(TEXT_FILTERS)
        self.file_model.setNameFilterDisables(False)  # hide non-matching files

        self.explore_view = QTreeView()
        self.explore_view.setModel(self.file_model)
        self.explore_view.setHeaderHidden(True)
        self.explore_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.explore_view.hideColumn(1)  # Size
        self.explore_view.hideColumn(2)  # Type
        self.explore_view.hideColumn(3)  # Date Modified
        self.explore_view.setIndentation(14)
        self.explore_view.setSortingEnabled(True)
        self.explore_view.setUniformRowHeights(True)
        tree_layout.addWidget(self.explore_view, 1)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        self.explorer_filter_checkbox = QCheckBox("Show all files")
        self.explorer_filter_checkbox.setToolTip("When unchecked, only text, document and image files are shown")
        self.explorer_filter_checkbox.stateChanged.connect(self.toggle_explorer_filter)
        filter_hint = QLabel("double-click to open")
        filter_hint.setObjectName("Hint")
        filter_row.addWidget(self.explorer_filter_checkbox)
        filter_row.addStretch(1)
        filter_row.addWidget(filter_hint)
        tree_layout.addLayout(filter_row)

        self.explore_stack.addWidget(welcome)
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
        """Kept for compatibility: the explorer footer is now static."""
        return None

    def show_directory_in_explorer(self, path):
        """Sets the file explorer root to the directory of the given path."""
        if not path:
            return
        folder_path = os.path.dirname(path) if os.path.isfile(path) else path
        self.file_model.setRootPath(folder_path)
        self.explore_view.setRootIndex(self.file_model.index(folder_path))
        self.explore_stack.setCurrentWidget(self.explore_view_widget)

    def create_new_folder(self):
        """Creates a new folder in the currently selected directory."""
        index = self.explore_view.currentIndex()
        if not index.isValid():
            dir_path = self.file_model.rootPath()
        else:
            dir_path = self.file_model.filePath(index)
            if not self.file_model.isDir(index):
                dir_path = self.file_model.filePath(index.parent())

        name, accepted = QInputDialog.getText(self, "New Folder", "Folder name:", text="New Folder")
        if not accepted or not name.strip():
            return
        if not self.file_model.mkdir(self.file_model.index(dir_path), name.strip()):
            QMessageBox.warning(self, "Could not create folder", f"Unable to create '{name}' in {dir_path}.")

    def toggle_explorer_filter(self, state):
        if state == Qt.Checked:
            self.file_model.setNameFilters([])
            self.file_model.setNameFilterDisables(True)
        else:
            self.file_model.setNameFilters(TEXT_FILTERS)
            self.file_model.setNameFilterDisables(False)

    def refresh_explorer(self):
        self.file_model.setRootPath(self.file_model.rootPath())

    # ------------------------------------------------------------------ settings
    def init_settings_tab(self) -> None:
        self.settings_tab, layout = self._scroll_page()

        appearance_card, appearance_layout = self._card(
            "Appearance", "Theme and typography for the editor."
        )
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(9)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        form.addRow("Theme", self.theme_combo)

        self.font_combo = QFontComboBox()
        font_policy = self.font_combo.sizePolicy()
        font_policy.setHorizontalPolicy(QSizePolicy.Ignored)
        self.font_combo.setSizePolicy(font_policy)
        form.addRow("Editor font", self.font_combo)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 30)
        form.addRow("Font size", self.font_size_spinbox)

        appearance_layout.addLayout(form)

        self.word_wrap_checkbox = QCheckBox("Wrap long lines")
        appearance_layout.addWidget(self.word_wrap_checkbox)
        layout.addWidget(appearance_card)

        sidebar_card, sidebar_layout = self._card("Sidebar", "Resize the workspace to fit your screen.")
        sidebar_form = QFormLayout()
        sidebar_form.setHorizontalSpacing(12)
        sidebar_form.setVerticalSpacing(9)

        (
            width_widget,
            self.sidebar_width_decrease_button,
            self.sidebar_width_label,
            self.sidebar_width_increase_button,
        ) = self._stepper("300")
        sidebar_form.addRow("Width", width_widget)

        (
            font_widget,
            self.sidebar_font_size_decrease_button,
            self.sidebar_font_size_label,
            self.sidebar_font_size_increase_button,
        ) = self._stepper("10")
        sidebar_form.addRow("Font size", font_widget)
        sidebar_layout.addLayout(sidebar_form)
        layout.addWidget(sidebar_card)

        about_card, about_layout = self._card("About StudyMate", None)
        about_text = QLabel(
            "Version 0.3.0 · offline-first AI.\n"
            "Summaries, key points and mind maps are generated locally on your machine."
        )
        about_text.setObjectName("Hint")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        layout.addWidget(about_card)

        layout.addStretch(1)

    # Keep old theme_button for compatibility with existing signal connections
    @property
    def theme_button(self):
        return self.theme_combo

    # ------------------------------------------------------------------ AI
    def init_ai_tab(self, icon=None) -> None:
        self.ai_tab, layout = self._scroll_page()

        summary_card, summary_layout = self._card(
            "Summarize", "Condense the active note into a short brief."
        )
        summary_form = QFormLayout()
        summary_form.setHorizontalSpacing(12)
        summary_form.setVerticalSpacing(9)
        self.summary_length_combo = QComboBox()
        self.summary_length_combo.addItems(["Short", "Medium", "Long"])
        self.summary_length_combo.setCurrentText("Medium")
        summary_form.addRow("Length", self.summary_length_combo)
        summary_layout.addLayout(summary_form)

        self.summarize_button = QPushButton("Summarize note")
        self.summarize_button.setObjectName("Primary")
        summary_layout.addWidget(self.summarize_button)
        layout.addWidget(summary_card)

        tools_card, tools_layout = self._card(
            "Study tools", "Pull out concepts or turn the note into a mind map."
        )
        self.key_points_button = QPushButton("Get key points")
        self.mind_map_button = QPushButton("Generate mind map")
        tools_layout.addWidget(self.key_points_button)
        tools_layout.addWidget(self.mind_map_button)
        layout.addWidget(tools_card)

        output_card, output_layout = self._card(
            "Result", "Send the result to your note or copy it elsewhere."
        )
        self.ai_status_label = QLabel("Idle")
        self.ai_status_label.setObjectName("Hint")
        output_layout.addWidget(self.ai_status_label)

        self.summary_output = QTextEdit()
        self.summary_output.setObjectName("AIOutput")
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("Summary will appear here...")
        self.summary_output.setMinimumHeight(140)
        output_layout.addWidget(self.summary_output)

        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        self.copy_output_button = QPushButton("Copy")
        self.copy_output_button.setObjectName("Ghost")
        self.insert_output_button = QPushButton("Insert")
        self.insert_output_button.setObjectName("Ghost")
        self.clear_output_button = QPushButton("Clear")
        self.clear_output_button.setObjectName("Ghost")
        action_row.addWidget(self.copy_output_button)
        action_row.addWidget(self.insert_output_button)
        action_row.addStretch(1)
        action_row.addWidget(self.clear_output_button)
        output_layout.addLayout(action_row)

        self.mind_map_preview = QLabel()
        self.mind_map_preview.setAlignment(Qt.AlignCenter)
        self.mind_map_preview.setMinimumHeight(160)
        self.mind_map_preview.hide()
        output_layout.addWidget(self.mind_map_preview)

        self.mind_map_text_output = QTextEdit()
        self.mind_map_text_output.setObjectName("AIOutput")
        self.mind_map_text_output.setReadOnly(True)
        self.mind_map_text_output.setPlaceholderText("Mind map outline will appear here...")
        self.mind_map_text_output.setMaximumHeight(120)
        self.mind_map_text_output.hide()
        output_layout.addWidget(self.mind_map_text_output)

        self.mind_map_export_button = QPushButton("Export mind map PNG")
        self.mind_map_export_button.hide()
        output_layout.addWidget(self.mind_map_export_button)
        layout.addWidget(output_card)

        external_card, external_layout = self._card(
            "External AI", "Open a web assistant for questions this app cannot answer."
        )
        self.gemini_button = QPushButton("Gemini")
        self.chatgpt_button = QPushButton("ChatGPT")
        self.copilot_button = QPushButton("Copilot")
        for button in (self.gemini_button, self.chatgpt_button, self.copilot_button):
            button.setObjectName("Ghost")
        external_row = QHBoxLayout()
        external_row.setSpacing(6)
        external_row.addWidget(self.gemini_button)
        external_row.addWidget(self.chatgpt_button)
        external_row.addWidget(self.copilot_button)
        external_layout.addLayout(external_row)
        layout.addWidget(external_card)
        layout.addStretch(1)

    # ------------------------------------------------------------------ events
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Emit the new width, but only when it's not collapsed to avoid spamming signals
        # during collapse/expand animations.
        if event.size().width() > 50 and event.oldSize().width() > 50:
            self.resized.emit(event.size().width())
