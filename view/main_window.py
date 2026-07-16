import os
from contextlib import suppress

from PyQt5.QtCore import Qt, QThreadPool, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QKeySequence, QTextOption
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from services.graph_visualizer import create_mind_map_pixmap, parse_indented_text
from services.lifecycle import LifecycleService
from services.mind_map_generator import MindMapWorker
from services.search_service import SearchService
from view.ai_workers import KeyPointsWorker, PreloadWorker, SummarizationWorker
from view.editor_area import EditorArea
from view.icons import app_icon
from view.markdown_preview import MarkdownPreviewDock
from view.menu_bar import MenuBar
from view.recent_files import RecentFilesManager
from view.settings_manager import SettingsManager
from view.shortcuts_dialog import ShortcutsDialog
from view.side_bar import SideBar
from view.status_bar import StatusBar
from view.toolbar import MainToolBar
from view.ui_controller import UIController
from view.update_checker import UpdateCheckWorker

APP_VERSION = "0.3.0"
PROJECT_URL = "https://github.com/smartnotes-application/smartnotes-application"
DEFAULT_EDITOR_FONT_SIZE = 11


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyMate")
        self.setWindowIcon(app_icon())
        self.resize(1400, 900)
        self.setAcceptDrops(True)

        self.sidebar_width = 300  # default; replaced by saved settings
        self.thread_pool = QThreadPool()
        self._last_mind_map_pixmap = None
        self._last_mind_map_text = ""
        self._syncing_sidebar = False

        # Persistence
        self.settings_manager = SettingsManager()
        self.settings_model = self.settings_manager.load_settings()
        self.recent_files = RecentFilesManager(self.settings_manager)

        # Menu + toolbar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.build_central_area()
        self.toolbar = MainToolBar(self.menu_bar.actions, self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Sidebar
        self.sidebar = SideBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.sidebar.collapse_requested.connect(self.toggle_sidebar_visibility)

        # Markdown preview dock
        self.preview_dock = MarkdownPreviewDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.preview_dock)
        self.preview_dock.hide()
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(250)
        self.preview_timer.timeout.connect(self.refresh_preview)

        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Apply persisted preferences before wiring the controller
        self.load_settings()

        # Controller and handlers (after widgets and settings exist)
        self.ui_controller = UIController(self)
        self.file_handler = self.ui_controller.file_handler
        self.tab_widget.tabCloseRequested.connect(self.file_handler.close_tab)

        self.connect_find_bar()
        self.connect_signals()

        self.restore_window_state()
        self.refresh_recent_menu()
        self.file_handler.new_file(is_initial_tab=True)

        # Preload AI models in the background
        self.preload_models()

    # ------------------------------------------------------------------ layout
    def build_central_area(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("EditorTabs")
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabBarAutoHide(False)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.build_find_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.find_bar)
        main_layout.addWidget(self.tab_widget, 1)

    def build_find_bar(self):
        self.find_bar = QFrame()
        self.find_bar.setObjectName("FindBar")
        outer = QVBoxLayout(self.find_bar)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(6)

        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Find in note...")
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace with...")
        self.find_case_sensitive_checkbox = QCheckBox("Match case", self)
        self.find_count_label = QLabel("")
        self.find_count_label.setObjectName("Hint")
        self.find_count_label.setMinimumWidth(70)
        self.find_prev_button = QPushButton("Previous", self)
        self.find_prev_button.setObjectName("Ghost")
        self.find_next_button = QPushButton("Next", self)
        self.find_next_button.setObjectName("Ghost")
        self.replace_button = QPushButton("Replace", self)
        self.replace_button.setObjectName("Ghost")
        self.replace_and_find_button = QPushButton("Replace & Find", self)
        self.replace_and_find_button.setObjectName("Ghost")
        self.replace_all_button = QPushButton("Replace All", self)
        self.replace_all_button.setObjectName("Ghost")
        self.close_find_button = QPushButton("✕", self)
        self.close_find_button.setObjectName("IconButton")
        self.close_find_button.setFixedSize(24, 24)
        self.close_find_button.setToolTip("Close find bar (Esc)")

        find_row = QHBoxLayout()
        find_row.setSpacing(6)
        find_row.addWidget(self.find_input, 1)
        find_row.addWidget(self.find_count_label)
        find_row.addWidget(self.find_case_sensitive_checkbox)
        find_row.addWidget(self.find_prev_button)
        find_row.addWidget(self.find_next_button)
        find_row.addWidget(self.close_find_button)

        replace_row = QHBoxLayout()
        replace_row.setSpacing(6)
        replace_row.addWidget(self.replace_input, 1)
        replace_row.addWidget(self.replace_button)
        replace_row.addWidget(self.replace_and_find_button)
        replace_row.addWidget(self.replace_all_button)

        outer.addLayout(find_row)
        outer.addLayout(replace_row)
        self.find_bar.hide()

        self._close_find_action = QAction(self)
        self._close_find_action.setShortcut(QKeySequence(Qt.Key_Escape))
        self._close_find_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self._close_find_action.triggered.connect(self.find_bar.hide)
        self.find_bar.addAction(self._close_find_action)

    def connect_find_bar(self):
        self.find_input.returnPressed.connect(self.find_next)
        self.find_input.textChanged.connect(self.update_find_count)
        self.find_case_sensitive_checkbox.stateChanged.connect(self.update_find_count)
        self.find_next_button.clicked.connect(self.find_next)
        self.find_prev_button.clicked.connect(self.find_previous)
        self.replace_button.clicked.connect(self.replace_current)
        self.replace_and_find_button.clicked.connect(self.replace_and_find)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_find_button.clicked.connect(self.find_bar.hide)

    # ------------------------------------------------------------------ wiring
    def connect_signals(self):
        # File menu
        self.menu_bar.actions["new"].triggered.connect(self.file_handler.new_file)
        self.menu_bar.actions["open"].triggered.connect(self.file_handler.open_file)
        self.menu_bar.actions["save"].triggered.connect(self.file_handler.save_file)
        self.menu_bar.actions["save_as"].triggered.connect(self.file_handler.save_file_as)
        self.menu_bar.actions["print"].triggered.connect(self.print_file)
        self.menu_bar.actions["export_pdf"].triggered.connect(self.export_to_pdf)
        self.menu_bar.actions["close"].triggered.connect(self.file_handler.close_current_file)
        self.menu_bar.actions["close_all"].triggered.connect(self.file_handler.close_all_files)
        self.menu_bar.actions["exit"].triggered.connect(self.close)

        # Edit menu
        self.menu_bar.actions["undo"].triggered.connect(
            lambda: self.current_editor().undo() if self.current_editor() else None
        )
        self.menu_bar.actions["redo"].triggered.connect(
            lambda: self.current_editor().redo() if self.current_editor() else None
        )
        self.menu_bar.actions["cut"].triggered.connect(
            lambda: self.current_editor().cut() if self.current_editor() else None
        )
        self.menu_bar.actions["copy"].triggered.connect(
            lambda: self.current_editor().copy() if self.current_editor() else None
        )
        self.menu_bar.actions["paste"].triggered.connect(
            lambda: self.current_editor().paste() if self.current_editor() else None
        )
        self.menu_bar.actions["select_all"].triggered.connect(
            lambda: self.current_editor().selectAll() if self.current_editor() else None
        )
        self.menu_bar.actions["replace"].triggered.connect(self.show_find_bar)

        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Delete)
        delete_action.triggered.connect(
            lambda: self.current_editor().textCursor().deleteChar()
            if self.current_editor()
            else None
        )
        self.addAction(delete_action)

        # AI menu
        self.menu_bar.actions["summarize"].triggered.connect(self.run_summarization)
        self.menu_bar.actions["key_points"].triggered.connect(self.run_key_points_extraction)
        self.menu_bar.actions["mind_map"].triggered.connect(self.run_mind_map_generation)
        self.menu_bar.actions["export_mind_map"].triggered.connect(self.export_mind_map)
        self.menu_bar.actions["study_plan"].triggered.connect(self.suggest_study_plan)

        # View menu
        self.menu_bar.actions["zoom_in"].triggered.connect(self.editor_zoom_in)
        self.menu_bar.actions["zoom_out"].triggered.connect(self.editor_zoom_out)
        self.menu_bar.actions["reset_zoom"].triggered.connect(self.reset_editor_zoom)
        self.menu_bar.actions["fullscreen"].triggered.connect(self.toggle_fullscreen)
        self.menu_bar.actions["toggle_sidebar"].triggered.connect(
            self.toggle_sidebar_visibility
        )
        self.menu_bar.actions["toggle_statusbar"].triggered.connect(
            self.toggle_statusbar_visibility
        )
        self.menu_bar.actions["dark_mode"].triggered.connect(self.toggle_dark_mode)
        self.menu_bar.actions["preview"].toggled.connect(self.set_preview_visible)
        self.preview_dock.visibilityChanged.connect(self.on_preview_visibility_changed)

        # Help menu
        self.menu_bar.actions["docs"].triggered.connect(self.show_documentation)
        self.menu_bar.actions["shortcuts"].triggered.connect(self.show_shortcuts)
        self.menu_bar.actions["check_updates"].triggered.connect(self.check_for_updates)
        self.menu_bar.actions["feedback"].triggered.connect(self.send_feedback)
        self.menu_bar.actions["about"].triggered.connect(self.show_about_dialog)
        self.menu_bar.actions["about_qt"].triggered.connect(QApplication.instance().aboutQt)

        # AI sidebar
        self.sidebar.summarize_button.clicked.connect(self.run_summarization)
        self.sidebar.key_points_button.clicked.connect(self.run_key_points_extraction)
        self.sidebar.mind_map_button.clicked.connect(self.run_mind_map_generation)
        self.sidebar.mind_map_export_button.clicked.connect(self.export_mind_map)
        self.sidebar.copy_output_button.clicked.connect(self.copy_ai_output)
        self.sidebar.insert_output_button.clicked.connect(self.insert_ai_output)
        self.sidebar.clear_output_button.clicked.connect(self.clear_ai_output)
        self.sidebar.gemini_button.clicked.connect(
            lambda: self.open_external_link("https://gemini.google.com/")
        )
        self.sidebar.chatgpt_button.clicked.connect(
            lambda: self.open_external_link("https://chat.openai.com/")
        )
        self.sidebar.copilot_button.clicked.connect(
            lambda: self.open_external_link("https://copilot.microsoft.com/")
        )

        # Settings tab
        self.sidebar.theme_combo.currentTextChanged.connect(self.set_theme)
        self.sidebar.font_combo.currentFontChanged.connect(self.set_editor_font)
        self.sidebar.font_size_spinbox.valueChanged.connect(self.set_editor_font_size)
        self.sidebar.word_wrap_checkbox.stateChanged.connect(self.set_word_wrap)
        self.sidebar.sidebar_width_increase_button.clicked.connect(
            lambda: self.change_sidebar_width(10)
        )
        self.sidebar.sidebar_width_decrease_button.clicked.connect(
            lambda: self.change_sidebar_width(-10)
        )
        self.sidebar.sidebar_font_size_increase_button.clicked.connect(
            lambda: self.change_sidebar_font_size(1)
        )
        self.sidebar.sidebar_font_size_decrease_button.clicked.connect(
            lambda: self.change_sidebar_font_size(-1)
        )
        self.sidebar.resized.connect(self.on_sidebar_manually_resized)
        self.sidebar.tabs.tabBarClicked.connect(self.handle_tab_bar_click)

        # Explorer tab
        self.sidebar.open_folder_button.clicked.connect(self.sidebar.open_folder_in_explorer)
        self.sidebar.open_file_button.clicked.connect(self.file_handler.open_file)
        self.sidebar.new_file_button.clicked.connect(self.file_handler.new_file)
        self.sidebar.new_file_action.triggered.connect(self.file_handler.new_file)
        self.sidebar.new_folder_action.triggered.connect(self.sidebar.create_new_folder)
        self.sidebar.refresh_action.triggered.connect(self.sidebar.refresh_explorer)
        self.sidebar.collapse_action.triggered.connect(self.sidebar.explore_view.collapseAll)
        self.sidebar.explore_view.doubleClicked.connect(self.on_explore_file_selected)

    def on_editor_created(self, editor):
        """Extra wiring applied to every new editor tab."""
        editor.textChanged.connect(self.schedule_preview_refresh)

    # ------------------------------------------------------------------ editing
    def current_editor(self) -> EditorArea | None:
        """Returns the currently active EditorArea widget, if any."""
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorArea):
            return widget
        return None

    def on_tab_changed(self, index):
        self.update_window_title()
        self.update_status_bar()
        self.refresh_preview()
        self.update_find_count()

    def on_modification_changed(self, editor, modified):
        """Updates the tab title with an asterisk when modified."""
        widget = editor
        if not isinstance(widget, EditorArea):
            return

        index = self.tab_widget.indexOf(widget)
        if index != -1:
            tab_text = self.tab_widget.tabText(index)
            if modified and not tab_text.endswith("*"):
                self.tab_widget.setTabText(index, tab_text + "*")
            elif not modified and tab_text.endswith("*"):
                self.tab_widget.setTabText(index, tab_text[:-1])
        self.update_window_title()

    def update_window_title(self):
        widget = self.tab_widget.currentWidget()
        if not widget:
            self.setWindowTitle("StudyMate")
            return

        file_path = getattr(widget, "file_path", None)
        title = os.path.basename(file_path) if file_path else "Untitled"

        if isinstance(widget, EditorArea) and widget.document().isModified():
            title += "*"

        self.setWindowTitle(f"{title} — StudyMate")

    def update_status_bar(self):
        editor = self.current_editor()
        self.status_bar.update_editor_info(editor)

    def on_explore_file_selected(self, index):
        file_path = self.sidebar.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.file_handler.open_file(file_path=file_path)

    # ------------------------------------------------------------------ recent files
    def remember_recent_file(self, file_path):
        self.recent_files.add(file_path)
        self.refresh_recent_menu()

    def refresh_recent_menu(self):
        menu = self.menu_bar.actions["recent_files_menu"]
        menu.clear()
        files = self.recent_files.files()
        if not files:
            empty_action = menu.addAction("No recent files")
            empty_action.setEnabled(False)
            return

        for path in files:
            action = menu.addAction(os.path.basename(path))
            action.setToolTip(path)
            action.triggered.connect(
                lambda checked=False, target=path: self.file_handler.open_file(target)
            )
        menu.addSeparator()
        clear_action = menu.addAction("Clear list")
        clear_action.triggered.connect(self.clear_recent_files)

    def clear_recent_files(self):
        self.recent_files.clear()
        self.refresh_recent_menu()
        self.status_bar.showMessage("Recent files cleared.", 3000)

    # ------------------------------------------------------------------ preview
    def schedule_preview_refresh(self):
        if self.preview_dock.isVisible():
            self.preview_timer.start()

    def refresh_preview(self):
        if not self.preview_dock.isVisible():
            return
        editor = self.current_editor()
        if editor is not None:
            self.preview_dock.set_source(
                editor.toPlainText(), self.settings_model.theme, editor.file_path or ""
            )
            return
        widget = self.tab_widget.currentWidget()
        file_path = getattr(widget, "file_path", "") if widget else ""
        self.preview_dock.set_source("", self.settings_model.theme, file_path)

    def set_preview_visible(self, visible, persist=True):
        self.preview_dock.setVisible(bool(visible))
        action = self.menu_bar.actions["preview"]
        action.blockSignals(True)
        action.setChecked(bool(visible))
        action.blockSignals(False)
        if visible:
            if self.preview_dock.width() < 320:
                self.resizeDocks([self.preview_dock], [420], Qt.Horizontal)
            self.refresh_preview()
        if persist:
            self.settings_manager.set_preview_visible(bool(visible))

    def on_preview_visibility_changed(self, visible):
        action = self.menu_bar.actions["preview"]
        action.blockSignals(True)
        action.setChecked(bool(visible))
        action.blockSignals(False)
        if visible:
            self.refresh_preview()

    # ------------------------------------------------------------------ AI actions
    def _ai_started(self, message: str, button):
        button.setEnabled(False)
        self.sidebar.ai_status_label.setText(message)
        self.status_bar.set_ai_status(message)
        self.status_bar.showMessage(message)

    def _ai_finished(self, message: str, button, status_message: str):
        button.setEnabled(True)
        self.sidebar.ai_status_label.setText(message)
        self.status_bar.set_ai_status("")
        self.status_bar.showMessage(status_message, 5000)

    def run_summarization(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Open a note to summarize.", 3000)
            return
        text_to_summarize = editor.toPlainText()
        if not text_to_summarize.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to summarize.")
            return

        length_option = self.sidebar.summary_length_combo.currentText()
        self._ai_started("Summarizing… (first run may download the model)", self.sidebar.summarize_button)
        self.sidebar.summary_output.setPlaceholderText("Summarizing... (this may take a moment on first run)")

        worker = SummarizationWorker(text_to_summarize, length_option)
        worker.signals.finished.connect(self.on_summarization_finished)
        worker.signals.error.connect(self.on_summarization_error)
        self.thread_pool.start(worker)

    def on_summarization_finished(self, summary):
        self.sidebar.summary_output.setText(summary)
        self.sidebar.summary_output.setPlaceholderText("Summary will appear here...")
        self._ai_finished("Summary ready", self.sidebar.summarize_button, "Summarization complete.")

    def on_summarization_error(self, error_message):
        self.sidebar.summary_output.setText(error_message)
        self.sidebar.summary_output.setPlaceholderText("Summary will appear here...")
        self._ai_finished("Summarization failed", self.sidebar.summarize_button, "Summarization error.")

    def run_key_points_extraction(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Open a note to analyse.", 3000)
            return
        text_to_analyze = editor.toPlainText()
        if not text_to_analyze.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to analyze.")
            return

        self._ai_started("Extracting key points…", self.sidebar.key_points_button)
        self.sidebar.summary_output.setText("Extracting key points...")

        worker = KeyPointsWorker(text_to_analyze)
        worker.signals.finished.connect(self.on_key_points_finished)
        worker.signals.error.connect(self.on_key_points_error)
        self.thread_pool.start(worker)

    def on_key_points_finished(self, key_points_text):
        self.sidebar.summary_output.setText(key_points_text)
        self._ai_finished("Key points ready", self.sidebar.key_points_button, "Key points extraction complete.")

    def on_key_points_error(self, error_message):
        self.sidebar.summary_output.setText(error_message)
        self._ai_finished("Key points failed", self.sidebar.key_points_button, "Key points extraction error.")

    def run_mind_map_generation(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Open a document to generate a mind map.", 3000)
            return
        text = editor.toPlainText()
        if not text.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to map.")
            return
        self._ai_started("Building mind map…", self.sidebar.mind_map_button)
        self.sidebar.mind_map_text_output.hide()
        self.sidebar.mind_map_preview.hide()
        self.sidebar.mind_map_export_button.hide()
        self.sidebar.summary_output.setText("Generating mind map...")

        worker = MindMapWorker(text)
        worker.signals.finished.connect(self.on_mind_map_finished)
        worker.signals.error.connect(self.on_mind_map_error)
        self.thread_pool.start(worker)

    def on_mind_map_finished(self, indented_text: str):
        self.sidebar.mind_map_text_output.setPlainText(indented_text)
        self.sidebar.mind_map_text_output.show()
        self.render_mind_map(indented_text)
        self.sidebar.summary_output.setText(indented_text)
        self._ai_finished("Mind map ready", self.sidebar.mind_map_button, "Mind map ready.")

    def render_mind_map(self, indented_text: str):
        self._last_mind_map_text = indented_text
        try:
            graph = parse_indented_text(indented_text)
            is_dark = self.settings_model.theme.lower() == "dark"
            pixmap = create_mind_map_pixmap(graph, is_dark)
        except Exception as e:
            self.status_bar.showMessage(f"Mind map render failed: {e}", 5000)
            self._last_mind_map_pixmap = None
            return

        if pixmap is None or pixmap.isNull():
            self.sidebar.mind_map_preview.hide()
            self.sidebar.mind_map_export_button.hide()
            self._last_mind_map_pixmap = None
            return

        width = max(220, self.sidebar.width() - 48)
        scaled = pixmap.scaledToWidth(width, Qt.SmoothTransformation)
        self.sidebar.mind_map_preview.setPixmap(scaled)
        self.sidebar.mind_map_preview.show()
        self.sidebar.mind_map_export_button.show()
        self._last_mind_map_pixmap = pixmap

    def on_mind_map_error(self, msg: str):
        self.sidebar.summary_output.setText(msg)
        self._ai_finished("Mind map failed", self.sidebar.mind_map_button, "Mind map error.")

    def export_mind_map(self):
        if self._last_mind_map_pixmap is None or self._last_mind_map_pixmap.isNull():
            self.status_bar.showMessage("No mind map to export.", 3000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Mind Map", "mindmap.png", "PNG Files (*.png);;All Files (*)"
        )
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            if self._last_mind_map_pixmap.save(path, "PNG"):
                self.status_bar.showMessage(f"Mind map exported to {os.path.basename(path)}", 5000)
            else:
                QMessageBox.warning(self, "Export failed", "Could not save mind map image.")

    def copy_ai_output(self):
        text = self.sidebar.summary_output.toPlainText()
        if not text.strip():
            self.status_bar.showMessage("Nothing to copy yet.", 3000)
            return
        QApplication.clipboard().setText(text)
        self.status_bar.showMessage("Result copied to clipboard.", 3000)

    def insert_ai_output(self):
        text = self.sidebar.summary_output.toPlainText().strip()
        if not text:
            self.status_bar.showMessage("Nothing to insert yet.", 3000)
            return
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Open a note to insert into.", 3000)
            return
        cursor = editor.textCursor()
        prefix = "" if cursor.atBlockStart() else "\n\n"
        cursor.insertText(prefix + text)
        editor.setTextCursor(cursor)
        self.status_bar.showMessage("Result inserted into the note.", 3000)

    def clear_ai_output(self):
        self.sidebar.summary_output.clear()
        self.sidebar.ai_status_label.setText("Idle")
        self.status_bar.set_ai_status("")

    def suggest_study_plan(self):
        editor = self.current_editor()
        text = editor.toPlainText().strip() if editor else ""
        if not text:
            QMessageBox.information(self, "Study Plan", "Open a document with notes to generate a plan.")
            return

        # Heuristic: headings/bullets become topics, otherwise the first sentences.
        topics = [
            line.strip(" -#*•")
            for line in text.splitlines()
            if line.strip().startswith(("#", "-", "*", "•")) or line.strip().endswith(":")
        ]
        if not topics:
            topics = [s.strip() for s in text.split(".") if s.strip()][:5]
        if not topics:
            topics = ["General review"]

        topics = [topic[:80] for topic in topics[:8]]
        plan_lines = ["Suggested study plan (Pomodoro 25/5):", ""]
        for index, topic in enumerate(topics, 1):
            plan_lines.append(f"{index}. {topic} — 25 min focus + 5 min break")
        plan_lines.append("")
        plan_lines.append(f"Total: ~{len(topics) * 30} min.")

        reply = QMessageBox.question(
            self,
            "Study Plan",
            "\n".join(plan_lines) + "\n\nAdd these topics to your task list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            for topic in topics:
                self.sidebar.scheduler_tab.add_task_title(topic)
            self.sidebar.tabs.setCurrentWidget(self.sidebar.scheduler_tab)
            self.status_bar.showMessage(f"Added {len(topics)} study tasks.", 5000)

    # ------------------------------------------------------------------ files
    def print_file(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Nothing to print.", 3000)
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            editor.document().print_(printer)
            self.status_bar.showMessage("Document sent to printer.", 4000)

    def export_to_pdf(self):
        """Exports the current content of the editor to a PDF file."""
        editor = self.current_editor()
        if not editor or not editor.toPlainText().strip():
            self.status_bar.showMessage("Nothing to export. The editor is empty.", 5000)
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        editor.document().print_(printer)
        self.status_bar.showMessage(f"Exported to {os.path.basename(file_path)}", 5000)

    # ------------------------------------------------------------------ theme & settings
    def toggle_dark_mode(self, checked):
        self.set_theme("dark" if checked else "light")

    def set_theme(self, theme_name):
        theme = (theme_name or "light").lower()
        if theme not in ("light", "dark"):
            theme = "light"
        self.settings_model.update_theme(theme)
        self.settings_model.save(self.settings_manager)
        self.apply_theme()

    def set_dark_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.apply_dark()

    def apply_dark_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.apply_dark()

    def apply_light_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.apply_light(self.sidebar)

    def apply_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.sync_ui(self.sidebar, self.menu_bar.actions, self.settings_model.theme)
        ThemeManager.apply(self.settings_model.theme)
        for index in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(index)
            if isinstance(widget, EditorArea):
                widget.apply_theme(self.settings_model.theme)
        self.preview_dock.set_theme(self.settings_model.theme)
        if self._last_mind_map_text:
            self.render_mind_map(self._last_mind_map_text)
        self.refresh_preview()

    def load_settings(self):
        self.apply_settings_to_ui()

    def apply_settings_to_ui(self):
        self.apply_theme()

        self.sidebar.font_combo.blockSignals(True)
        self.sidebar.font_combo.setCurrentFont(
            QFont(self.settings_model.editor_font_family, self.settings_model.editor_font_size)
        )
        self.sidebar.font_combo.blockSignals(False)

        self.sidebar.font_size_spinbox.blockSignals(True)
        self.sidebar.font_size_spinbox.setValue(self.settings_model.editor_font_size)
        self.sidebar.font_size_spinbox.blockSignals(False)

        self.apply_editor_font_size(self.settings_model.editor_font_size)
        self.apply_sidebar_width(self.settings_model.sidebar_width)
        self.apply_sidebar_font_size(self.settings_model.sidebar_font_size)

        self.sidebar.word_wrap_checkbox.blockSignals(True)
        self.sidebar.word_wrap_checkbox.setChecked(self.settings_model.word_wrap)
        self.sidebar.word_wrap_checkbox.blockSignals(False)
        self.apply_word_wrap(Qt.Checked if self.settings_model.word_wrap else Qt.Unchecked)

    def set_editor_font(self, font):
        self.settings_model.update_editor_font_family(font.family())
        self.settings_model.save(self.settings_manager)
        self.apply_editor_font_family(font.family())

    def apply_editor_font_family(self, font_family):
        new_font = QFont(font_family, self.settings_model.editor_font_size)
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorArea):
                widget.setFont(new_font)

    def set_editor_font_size(self, size):
        size = max(8, min(30, int(size)))
        self.settings_model.update_editor_font_size(size)
        self.settings_model.save(self.settings_manager)
        self.apply_editor_font_size(size)

    def apply_editor_font_size(self, size):
        self.sidebar.font_size_spinbox.blockSignals(True)
        self.sidebar.font_size_spinbox.setValue(size)
        self.sidebar.font_size_spinbox.blockSignals(False)

        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorArea):
                font = widget.font()
                font.setPointSize(size)
                widget.setFont(font)

    def change_sidebar_width(self, delta):
        try:
            current_width = int(self.sidebar.sidebar_width_label.text())
        except ValueError:
            current_width = self.sidebar_width
        self.set_sidebar_width(max(240, min(600, current_width + delta)))

    def set_sidebar_width(self, width):
        width = max(240, min(600, int(width)))
        self.sidebar_width = width
        self.settings_model.update_sidebar_width(width)
        self.settings_model.save(self.settings_manager)
        self.apply_sidebar_width(width)

    def apply_sidebar_width(self, width):
        self.sidebar.sidebar_width_label.setText(str(width))
        if self.sidebar.isVisible() and self.sidebar.width() > 50:
            self._syncing_sidebar = True
            try:
                self.resizeDocks([self.sidebar], [width], Qt.Horizontal)
            finally:
                self._syncing_sidebar = False

    def on_sidebar_manually_resized(self, width):
        if self._syncing_sidebar:
            return
        self.sidebar_width = width
        self.settings_model.update_sidebar_width(width)
        self.settings_model.save(self.settings_manager)
        self.sidebar.sidebar_width_label.blockSignals(True)
        self.sidebar.sidebar_width_label.setText(str(width))
        self.sidebar.sidebar_width_label.blockSignals(False)

    def change_sidebar_font_size(self, delta):
        try:
            current_size = int(self.sidebar.sidebar_font_size_label.text())
        except ValueError:
            current_size = self.settings_model.sidebar_font_size
        self.set_sidebar_font_size(max(8, min(20, current_size + delta)))

    def set_sidebar_font_size(self, size):
        self.settings_model.update_sidebar_font_size(size)
        self.settings_model.save(self.settings_manager)
        self.apply_sidebar_font_size(size)

    def apply_sidebar_font_size(self, size):
        self.sidebar.sidebar_font_size_label.setText(str(size))
        container = self.sidebar.widget()
        font = container.font()
        font.setPointSize(size)
        container.setFont(font)

    def apply_word_wrap(self, state):
        enabled = state == Qt.Checked
        mode = QTextOption.WordWrap if enabled else QTextOption.NoWrap
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorArea):
                widget.setWordWrapMode(mode)

    def set_word_wrap(self, state):
        enabled = state == Qt.Checked
        self.settings_model.update_word_wrap(enabled)
        self.settings_model.save(self.settings_manager)
        self.apply_word_wrap(state)

    # ------------------------------------------------------------------ view
    def editor_zoom_in(self):
        self.set_editor_font_size(self.settings_model.editor_font_size + 1)

    def editor_zoom_out(self):
        self.set_editor_font_size(self.settings_model.editor_font_size - 1)

    def reset_editor_zoom(self):
        self.set_editor_font_size(DEFAULT_EDITOR_FONT_SIZE)

    def toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showMaximized()

    def toggle_sidebar_visibility(self, checked=None):
        target = (not self.sidebar.isVisible()) if checked is None else bool(checked)
        self.sidebar.setVisible(target)
        action = self.menu_bar.actions["toggle_sidebar"]
        action.blockSignals(True)
        action.setChecked(target)
        action.blockSignals(False)
        self.settings_manager.set_sidebar_visible(target)

    def toggle_statusbar_visibility(self, checked=None):
        target = (not self.status_bar.isVisible()) if checked is None else bool(checked)
        self.status_bar.setVisible(target)
        action = self.menu_bar.actions["toggle_statusbar"]
        action.blockSignals(True)
        action.setChecked(target)
        action.blockSignals(False)
        self.settings_manager.set_status_bar_visible(target)

    def handle_tab_bar_click(self, index):
        # Clicking the sidebar tabs always brings a hidden sidebar back.
        if not self.sidebar.isVisible():
            self.toggle_sidebar_visibility(True)

    # ------------------------------------------------------------------ window state
    @property
    def maximized_on_close(self) -> bool:
        return self.settings_manager.get_window_maximized()

    def restore_window_state(self):
        geometry = self.settings_manager.get_window_geometry()
        if geometry:
            with suppress(Exception):
                self.restoreGeometry(geometry)

        sidebar_visible = self.settings_manager.get_sidebar_visible()
        self.sidebar.setVisible(sidebar_visible)
        self.menu_bar.actions["toggle_sidebar"].setChecked(sidebar_visible)

        status_visible = self.settings_manager.get_status_bar_visible()
        self.status_bar.setVisible(status_visible)
        self.menu_bar.actions["toggle_statusbar"].setChecked(status_visible)

        self.set_preview_visible(self.settings_manager.get_preview_visible(), persist=False)

    def save_window_state(self):
        self.settings_manager.setValue("windowGeometry", self.saveGeometry())
        self.settings_manager.setValue("windowState", self.saveState())
        self.settings_manager.set_window_maximized(self.isMaximized())
        self.settings_manager.set_sidebar_visible(self.sidebar.isVisible())
        self.settings_manager.set_status_bar_visible(self.status_bar.isVisible())
        self.settings_manager.set_preview_visible(self.preview_dock.isVisible())
        self.settings_manager.sync()

    def closeEvent(self, event):
        """Handles the window close event."""
        if not LifecycleService.confirm_shutdown(self.file_handler, self.settings_manager):
            event.ignore()
            return

        self.save_window_state()
        event.accept()

    # ------------------------------------------------------------------ drag & drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        handled = False
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if os.path.isfile(path):
                self.file_handler.open_file(path)
                handled = True
            elif os.path.isdir(path):
                self.sidebar.show_directory_in_explorer(path)
                handled = True
        if handled:
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    # ------------------------------------------------------------------ find / replace
    def show_find_bar(self):
        self.find_bar.show()
        self.find_input.setFocus()
        self.find_input.selectAll()
        self.update_find_count()

    def update_find_count(self):
        editor = self.current_editor()
        query = self.find_input.text().strip() if hasattr(self, "find_input") else ""
        if not isinstance(editor, EditorArea) or not query:
            self.find_count_label.setText("")
            return
        total = SearchService.count_matches(
            editor.toPlainText(), query, self.find_case_sensitive_checkbox.isChecked()
        )
        self.find_count_label.setText(f"{total} match{'es' if total != 1 else ''}")

    def find_next(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Find is only available in text editors.", 3000)
            return

        query = self.find_input.text()
        if not query:
            self.status_bar.showMessage("Enter search text before finding.", 3000)
            return

        found = SearchService.find_next(
            editor, query, self.find_case_sensitive_checkbox.isChecked()
        )
        if not found:
            self.status_bar.showMessage(f"No matches found for '{query}'", 3000)
        self.update_find_count()

    def find_previous(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Find is only available in text editors.", 3000)
            return

        query = self.find_input.text()
        if not query:
            self.status_bar.showMessage("Enter search text before moving to the previous match.", 3000)
            return

        found = SearchService.find_previous(
            editor, query, self.find_case_sensitive_checkbox.isChecked()
        )
        if not found:
            self.status_bar.showMessage(f"No matches found for '{query}'", 3000)

    def replace_text(self):
        self.show_find_bar()

    def replace_current(self):
        editor = self.current_editor()
        if not editor:
            return

        query = self.find_input.text()
        replace_text = self.replace_input.text()
        if not query:
            self.status_bar.showMessage("Enter text to find before replacing.", 3000)
            return

        replaced = SearchService.replace_current(
            editor, query, replace_text, self.find_case_sensitive_checkbox.isChecked()
        )
        self.status_bar.showMessage(
            "Replaced current selection." if replaced else "No matching selection to replace.",
            2000,
        )
        self.update_find_count()

    def replace_and_find(self):
        self.replace_current()
        self.find_next()

    def replace_all(self):
        editor = self.current_editor()
        if not editor:
            return

        query = self.find_input.text()
        replace_text = self.replace_input.text()
        if not query:
            self.status_bar.showMessage("Enter text to find before replacing.", 3000)
            return

        original_text = editor.toPlainText()
        new_text, replacements = SearchService.replace_all(
            original_text, query, replace_text, self.find_case_sensitive_checkbox.isChecked()
        )

        if replacements == 0:
            self.status_bar.showMessage(f"No occurrences of '{query}' found.", 3000)
            return

        editor.setPlainText(new_text)
        editor.document().setModified(True)
        self.status_bar.showMessage(f"Replaced {replacements} occurrences of '{query}'.", 3000)
        self.update_find_count()

    # ------------------------------------------------------------------ help & updates
    def open_external_link(self, url_string):
        url = QUrl(url_string)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self, "Browser error", f"Could not open:\n{url_string}\n\nPlease open it manually."
            )
            self.status_bar.showMessage(f"Failed to open {url_string}", 4000)
        else:
            self.status_bar.showMessage(f"Opened {url.host()}", 3000)

    def show_documentation(self):
        QMessageBox.information(
            self,
            "Documentation",
            "StudyMate quick guide\n\n"
            "• File → New / Open / Save, multi-tab editor, find & replace (Ctrl+F)\n"
            "• Drag files onto the window to open them\n"
            "• Markdown preview: View → Markdown Preview (Ctrl+Shift+M)\n"
            "• AI tab: Summarize, Key Points, Generate Mind Map (+ Export PNG)\n"
            "• Tasks tab: add tasks, set priority, filter and track progress\n"
            "• Settings: theme, font, sidebar width, word wrap\n\n"
            "Keyboard shortcuts: Help → Keyboard Shortcuts (Ctrl+/)",
        )

    def show_shortcuts(self):
        ShortcutsDialog(self).exec_()

    def check_for_updates(self):
        self.status_bar.showMessage("Checking for updates…")
        worker = UpdateCheckWorker()
        worker.signals.finished.connect(self.on_update_available)
        worker.signals.error.connect(self.on_update_error)
        self.thread_pool.start(worker)

    def on_update_available(self, tag, url):
        current = APP_VERSION
        if tag.lstrip("vV") == current:
            QMessageBox.information(
                self, "Updates", f"StudyMate {current} is the latest version."
            )
            self.status_bar.showMessage("You are up to date.", 4000)
            return

        box = QMessageBox(self)
        box.setWindowTitle("Update available")
        box.setIcon(QMessageBox.Information)
        box.setText(f"StudyMate {tag} is available.")
        box.setInformativeText(f"You are running version {current}.")
        open_button = box.addButton("Open release page", QMessageBox.AcceptRole)
        box.addButton("Later", QMessageBox.RejectRole)
        box.exec_()
        if box.clickedButton() is open_button:
            QDesktopServices.openUrl(QUrl(url))
        self.status_bar.showMessage(f"Latest release: {tag}", 5000)

    def on_update_error(self, message):
        QMessageBox.warning(
            self,
            "Updates",
            f"Could not check for updates:\n{message}\n\n"
            "Check your connection or visit GitHub to check manually.",
        )
        self.status_bar.showMessage("Update check failed.", 4000)

    def send_feedback(self):
        if not QDesktopServices.openUrl(QUrl(f"{PROJECT_URL}/issues/new")):
            QMessageBox.warning(self, "Feedback", "Could not open the feedback page in a browser.")
            return
        self.status_bar.showMessage("Opened feedback page in browser.", 3000)

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About StudyMate",
            f"<h3>StudyMate {APP_VERSION}</h3>"
            "<p>Local-first notes, PDF reading, AI summaries, key points and mind maps.</p>"
            "<p>Python 3.11+ · PyQt5 · Hugging Face transformers<br>"
            "Licensed MIT — see LICENSE.<br>© 2026 StudyMate contributors.</p>",
        )

    # ------------------------------------------------------------------ background
    def preload_models(self):
        self.thread_pool.start(PreloadWorker())
