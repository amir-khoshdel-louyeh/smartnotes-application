from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QAction, QTextEdit, QWidget, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QVBoxLayout, QTabWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QFont, QTextOption, QDesktopServices, QTextDocument, QTextCursor, QKeySequence
import re
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QUrl
from view.menu_bar import MenuBar
from view.side_bar import SideBar
from view.editor_area import EditorArea
from view.settings_manager import SettingsManager
from view.settings_model import SettingsModel
from view.status_bar import StatusBar
from view.ui_controller import UIController
from view.ai_workers import SummarizationWorker, KeyPointsWorker, PreloadWorker
from services.search_service import SearchService
from services.lifecycle import LifecycleService
from services.mind_map_generator import MindMapWorker
from services.graph_visualizer import parse_indented_text, create_mind_map_pixmap
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudyMate")
        self.setGeometry(100, 100, 1400, 900)
        self.sidebar_width = 300 # Default/initial width
        self.thread_pool = QThreadPool()
        self._last_mind_map_pixmap = None
        self._last_mind_map_text = ""

        # Menu Bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Tabbed Editor Area
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True) # More compact look
        self.tab_widget.setTabBarAutoHide(True) # Hide tab bar if only one tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # --- Find Bar (initially hidden) ---
        self.find_bar = QWidget(self)
        find_layout = QHBoxLayout(self.find_bar)
        find_layout.setContentsMargins(5, 5, 5, 5)
        find_layout.setSpacing(5)

        # --- Widgets ---
        self.find_input = QLineEdit(self)
        self.find_input.setPlaceholderText("Find...")
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Replace with...")
        self.find_case_sensitive_checkbox = QCheckBox("Case Sensitive", self)
        self.find_next_button = QPushButton("Next", self)
        self.find_prev_button = QPushButton("Previous", self)
        self.replace_button = QPushButton("Replace", self)
        self.replace_and_find_button = QPushButton("Replace & Find", self)
        self.replace_all_button = QPushButton("Replace All", self)
        close_find_button = QPushButton("Close", self)

        # --- Layout ---
        find_v_layout = QVBoxLayout()
        find_v_layout.addWidget(self.find_input)
        find_v_layout.addWidget(self.replace_input)
        find_layout.addLayout(find_v_layout)
        find_layout.addWidget(self.find_case_sensitive_checkbox)
        find_layout.addWidget(self.find_next_button)
        find_layout.addWidget(self.find_prev_button)
        find_layout.addWidget(self.replace_button)
        find_layout.addWidget(self.replace_and_find_button)
        find_layout.addWidget(self.replace_all_button)
        find_layout.addWidget(close_find_button, 0, Qt.AlignRight)
        self.find_bar.hide()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.find_bar)
        main_layout.addWidget(self.tab_widget)
        
        # Side Bar
        self.sidebar = SideBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)

        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Load settings through the manager/model layer
        self.settings_manager = SettingsManager()
        self.settings_model = self.settings_manager.load_settings()
        self.load_settings()

        # Controller and handlers (must be initialized after widgets and settings)
        self.ui_controller = UIController(self)
        self.file_handler = self.ui_controller.file_handler

        # Connect signals that depend on handlers
        self.tab_widget.tabCloseRequested.connect(self.file_handler.close_tab)

        # Connect find bar signals
        # Note: self.editor is now self.current_editor()
        self.find_input.returnPressed.connect(self.find_next_button.click)
        self.find_next_button.clicked.connect(self.find_next)
        self.find_prev_button.clicked.connect(self.find_previous)
        self.replace_button.clicked.connect(self.replace_current)
        self.replace_and_find_button.clicked.connect(self.replace_and_find)
        self.replace_all_button.clicked.connect(self.replace_all)
        close_find_button.clicked.connect(self.find_bar.hide)

        self.connect_signals()

        # Preload AI models in the background
        self.preload_models()

    def current_editor(self) -> EditorArea:
        """Returns the currently active EditorArea widget."""
        widget = self.tab_widget.currentWidget()
        # Return the widget only if it's an EditorArea, otherwise None
        if isinstance(widget, EditorArea):
            return widget
        return None

    def on_tab_changed(self, index):
        """Handles logic when the active tab changes."""
        self.update_window_title()
        self.update_status_bar()

    def preload_models(self):
        self.thread_pool.start(PreloadWorker())

    def closeEvent(self, event):
        """Handles the window close event."""
        if not LifecycleService.confirm_shutdown(self.file_handler, self.settings_manager):
            event.ignore()
            return

        event.accept()

    def connect_signals(self):
        # File Menu
        self.menu_bar.actions["new"].triggered.connect(self.file_handler.new_file)
        self.menu_bar.actions["open"].triggered.connect(self.file_handler.open_file)
        self.menu_bar.actions["save"].triggered.connect(self.file_handler.save_file)
        self.menu_bar.actions["save_as"].triggered.connect(self.file_handler.save_file_as)
        self.menu_bar.actions["print"].triggered.connect(self.print_file)
        self.menu_bar.actions["export_pdf"].triggered.connect(self.export_to_pdf) # Can be moved later
        self.menu_bar.actions["close"].triggered.connect(self.file_handler.close_current_file)
        self.menu_bar.actions["close_all"].triggered.connect(self.file_handler.close_all_files)
        self.menu_bar.actions["exit"].triggered.connect(self.close)

        # Edit Menu
        # These actions are now connected dynamically or need a wrapper
        self.menu_bar.undo_action.triggered.connect(lambda: self.current_editor().undo() if self.current_editor() else None)
        self.menu_bar.redo_action.triggered.connect(lambda: self.current_editor().redo() if self.current_editor() else None)
        self.menu_bar.cut_action.triggered.connect(lambda: self.current_editor().cut() if self.current_editor() else None)
        self.menu_bar.copy_action.triggered.connect(lambda: self.current_editor().copy() if self.current_editor() else None)
        self.menu_bar.paste_action.triggered.connect(lambda: self.current_editor().paste() if self.current_editor() else None)
        # For delete, we can use the editor's delete function directly
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Delete)
        delete_action.triggered.connect(lambda: self.current_editor().textCursor().deleteChar() if self.current_editor() else None)
        self.addAction(delete_action) # Add as a top-level action to catch the shortcut
        self.menu_bar.actions["select_all"].triggered.connect(lambda: self.current_editor().selectAll() if self.current_editor() else None)
        self.menu_bar.actions["replace"].triggered.connect(self.replace_text)
        # Connect Ctrl+F to the replace_text method as well
        find_shortcut_action = QAction(self)
        find_shortcut_action.setShortcut(QKeySequence.Find)
        find_shortcut_action.triggered.connect(self.replace_text)
        self.addAction(find_shortcut_action)

        # View Menu
        self.menu_bar.actions["zoom_in"].triggered.connect(self.editor_zoom_in)
        self.menu_bar.actions["zoom_out"].triggered.connect(self.editor_zoom_out)
        self.menu_bar.actions["reset_zoom"].triggered.connect(self.reset_editor_zoom)
        self.menu_bar.actions["fullscreen"].triggered.connect(self.toggle_fullscreen)
        self.menu_bar.actions["toggle_sidebar"].triggered.connect(self.toggle_sidebar_visibility)
        self.menu_bar.actions["toggle_statusbar"].triggered.connect(self.toggle_statusbar_visibility)
        self.menu_bar.actions["dark_mode"].triggered.connect(self.toggle_dark_mode)

        # Help Menu
        self.menu_bar.actions["docs"].triggered.connect(self.show_documentation)
        self.menu_bar.actions["check_updates"].triggered.connect(self.check_for_updates)
        self.menu_bar.actions["feedback"].triggered.connect(self.send_feedback)
        self.menu_bar.actions["about"].triggered.connect(self.show_about_dialog)
        self.menu_bar.actions["about_qt"].triggered.connect(QApplication.instance().aboutQt)

        # --- Sidebar signals ---
        # AI Tab
        self.sidebar.summarize_button.clicked.connect(self.run_summarization)
        self.sidebar.key_points_button.clicked.connect(self.run_key_points_extraction)
        self.sidebar.mind_map_button.clicked.connect(self.run_mind_map_generation)
        self.sidebar.mind_map_export_button.clicked.connect(self.export_mind_map)
        self.sidebar.gemini_button.clicked.connect(lambda: self.open_external_link("https://gemini.google.com/"))
        self.sidebar.chatgpt_button.clicked.connect(lambda: self.open_external_link("https://chat.openai.com/"))
        self.sidebar.copilot_button.clicked.connect(lambda: self.open_external_link("https://copilot.microsoft.com/"))
        # Scheduler Tab
        # Settings Tab
        self.sidebar.theme_combo.currentTextChanged.connect(self.set_theme)
        self.sidebar.font_combo.currentFontChanged.connect(self.set_editor_font)
        self.sidebar.font_size_spinbox.valueChanged.connect(self.set_editor_font_size)
        self.sidebar.word_wrap_checkbox.stateChanged.connect(self.set_word_wrap)
        self.sidebar.sidebar_width_increase_button.clicked.connect(lambda: self.change_sidebar_width(10))
        self.sidebar.sidebar_width_decrease_button.clicked.connect(lambda: self.change_sidebar_width(-10))
        self.sidebar.sidebar_font_size_increase_button.clicked.connect(lambda: self.change_sidebar_font_size(1))
        self.sidebar.sidebar_font_size_decrease_button.clicked.connect(lambda: self.change_sidebar_font_size(-1))
        self.sidebar.resized.connect(self.on_sidebar_manually_resized)
        self.sidebar.tabs.tabBarClicked.connect(self.handle_tab_bar_click)
        # Explore Tab
        # The buttons are now connected inside side_bar.py to self.parent() which is this MainWindow instance
        self.sidebar.open_folder_button.clicked.connect(self.sidebar.open_folder_in_explorer)
        self.sidebar.open_file_button.clicked.connect(self.file_handler.open_file)
        self.sidebar.new_file_button.clicked.connect(self.file_handler.new_file)
        # Toolbar actions in sidebar
        self.sidebar.new_file_action.triggered.connect(self.file_handler.new_file)
        self.sidebar.new_folder_action.triggered.connect(self.sidebar.create_new_folder)
        self.sidebar.refresh_action.triggered.connect(self.sidebar.refresh_explorer)
        self.sidebar.collapse_action.triggered.connect(self.sidebar.explore_view.collapseAll)
        self.sidebar.explore_view.doubleClicked.connect(self.on_explore_file_selected)

    def open_external_link(self, url_string):
        url = QUrl(url_string)
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "Browser error", f"Could not open:\n{url_string}\n\nPlease open it manually.")
            self.status_bar.showMessage(f"Failed to open {url_string}", 4000)
        else:
            self.status_bar.showMessage(f"Opened {url.host()}", 3000)

    def on_modification_changed(self, editor, modified):
        """Updates the tab title with an asterisk when modified."""
        widget = editor
        if not isinstance(widget, EditorArea): # Should always be an editor, but good practice to check
            return

        index = self.tab_widget.indexOf(widget)
        if index != -1:
            tab_text = self.tab_widget.tabText(index)
            # Prevent adding multiple asterisks
            if modified and not tab_text.endswith('*'):
                self.tab_widget.setTabText(index, tab_text + '*')
            elif not modified and tab_text.endswith('*'):
                self.tab_widget.setTabText(index, tab_text[:-1])
        self.update_window_title()

    def on_explore_file_selected(self, index):
        file_path = self.sidebar.file_model.filePath(index)
        # Check if it's a file, not a directory
        if os.path.isfile(file_path):
            self.file_handler.open_file(file_path=file_path)

    def run_summarization(self):
        editor = self.current_editor()
        if not editor: return
        text_to_summarize = editor.toPlainText()
        if not text_to_summarize.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to summarize.")
            return

        self.sidebar.summarize_button.setEnabled(False)
        self.sidebar.summary_output.setPlaceholderText("Summarizing... (this may take a moment on first run)")
        self.status_bar.showMessage("Starting summarization...")

        length_option = self.sidebar.summary_length_combo.currentText()

        worker = SummarizationWorker(text_to_summarize, length_option)
        worker.signals.finished.connect(self.on_summarization_finished)
        worker.signals.error.connect(self.on_summarization_error)
        self.thread_pool.start(worker)

    def on_summarization_finished(self, summary):
        self.sidebar.summary_output.setText(summary)
        self.sidebar.summarize_button.setEnabled(True)
        self.status_bar.showMessage("Summarization complete.", 5000)
        self.sidebar.summary_output.setPlaceholderText("Summary will appear here...")

    def on_summarization_error(self, error_message):
        self.sidebar.summary_output.setText(error_message)
        self.sidebar.summarize_button.setEnabled(True)
        self.status_bar.showMessage("Summarization error.", 5000)
        self.sidebar.summary_output.setPlaceholderText("Summary will appear here...")

    def run_key_points_extraction(self):
        editor = self.current_editor()
        if not editor: return
        text_to_analyze = editor.toPlainText()
        if not text_to_analyze.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to analyze.")
            return

        self.sidebar.key_points_button.setEnabled(False)
        self.sidebar.summary_output.setText("Extracting key points...")
        self.status_bar.showMessage("Starting key points extraction...")


        worker = KeyPointsWorker(text_to_analyze)
        worker.signals.finished.connect(self.on_key_points_finished)
        worker.signals.error.connect(self.on_key_points_error)
        self.thread_pool.start(worker)

    def on_key_points_finished(self, key_points_text):
        self.sidebar.summary_output.setText(key_points_text)
        self.sidebar.key_points_button.setEnabled(True)
        self.status_bar.showMessage("Key points extraction complete.", 5000)

    def on_key_points_error(self, error_message):
        self.sidebar.summary_output.setText(error_message)
        self.sidebar.key_points_button.setEnabled(True)
        self.status_bar.showMessage("Key points extraction error.", 5000)

    def run_mind_map_generation(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Open a document to generate a mind map.", 3000)
            return
        text = editor.toPlainText()
        if not text.strip():
            self.sidebar.summary_output.setText("Editor is empty. Nothing to map.")
            return
        self.sidebar.mind_map_button.setEnabled(False)
        self.sidebar.mind_map_text_output.hide()
        self.sidebar.mind_map_preview.hide()
        self.sidebar.mind_map_export_button.hide()
        self.sidebar.summary_output.setText("Generating mind map...")
        self.status_bar.showMessage("Generating mind map...")
        worker = MindMapWorker(text)
        worker.signals.finished.connect(self.on_mind_map_finished)
        worker.signals.error.connect(self.on_mind_map_error)
        self.thread_pool.start(worker)

    def on_mind_map_finished(self, indented_text: str):
        self._last_mind_map_text = indented_text
        self.sidebar.mind_map_text_output.setPlainText(indented_text)
        self.sidebar.mind_map_text_output.show()
        try:
            graph = parse_indented_text(indented_text)
            is_dark = self.settings_model.theme.lower() == "dark"
            pixmap = create_mind_map_pixmap(graph, is_dark)
            if not pixmap.isNull():
                # scale to sidebar width while keeping aspect
                w = max(260, self.sidebar.width() - 20)
                scaled = pixmap.scaledToWidth(w, Qt.SmoothTransformation)
                self.sidebar.mind_map_preview.setPixmap(scaled)
                self.sidebar.mind_map_preview.show()
                self._last_mind_map_pixmap = pixmap
                self.sidebar.mind_map_export_button.show()
            else:
                self.sidebar.mind_map_preview.hide()
                self._last_mind_map_pixmap = None
        except Exception as e:
            self.status_bar.showMessage(f"Mind map render failed: {e}", 5000)
            self._last_mind_map_pixmap = None
        self.sidebar.mind_map_button.setEnabled(True)
        self.sidebar.summary_output.setText(indented_text)
        self.status_bar.showMessage("Mind map ready.", 5000)

    def on_mind_map_error(self, msg: str):
        self.sidebar.summary_output.setText(msg)
        self.sidebar.mind_map_button.setEnabled(True)
        self.status_bar.showMessage("Mind map error.", 5000)

    def export_mind_map(self):
        if self._last_mind_map_pixmap is None or self._last_mind_map_pixmap.isNull():
            self.status_bar.showMessage("No mind map to export.", 3000)
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Mind Map", "mindmap.png", "PNG Files (*.png);;All Files (*)")
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            if self._last_mind_map_pixmap.save(path, "PNG"):
                self.status_bar.showMessage(f"Mind map exported to {os.path.basename(path)}", 5000)
            else:
                QMessageBox.warning(self, "Export failed", "Could not save mind map image.")

    def suggest_study_plan(self):
        editor = self.current_editor()
        text = editor.toPlainText().strip() if editor else ""
        if not text:
            QMessageBox.information(self, "Study Plan", "Open a document with notes to generate a plan.")
            return
        # Heuristic: split into topics by headings / blank lines, suggest 25-min pomodoro per topic
        topics = [line.strip(" -#*") for line in text.splitlines() if line.strip().startswith(("#", "-", "*", "•")) or line.strip().endswith(":")]
        if not topics:
            # fallback: first sentences as topics
            sentences = [s.strip() for s in text.split(".") if s.strip()][:5]
            topics = sentences
        if not topics:
            topics = ["General review"]
        plan_lines = ["Suggested Study Plan (Pomodoro 25/5):", ""]
        for i, t in enumerate(topics[:8], 1):
            plan_lines.append(f"{i}. {t[:80]} — 25 min focus + 5 min break")
        plan_lines.append("")
        plan_lines.append(f"Total: ~{len(topics[:8])*30} min. Tip: check tasks in Scheduler tab.")
        QMessageBox.information(self, "Study Plan", "\n".join(plan_lines))

    def editor_zoom_in(self):
        editor = self.current_editor()
        if not editor: return
        editor.zoomIn()
        current_size = editor.font().pointSize()
        self.set_editor_font_size(current_size)

    def editor_zoom_out(self):
        editor = self.current_editor()
        if not editor: return
        editor.zoomOut()
        current_size = editor.font().pointSize()
        self.set_editor_font_size(current_size)

    def toggle_sidebar_visibility(self):
        # A width of 0 would hide the dock widget completely.
        # A small width will collapse the content but keep the tab bar visible.
        is_currently_expanded = self.sidebar.width() > 50

        if is_currently_expanded:
            self.sidebar_width = self.sidebar.width() # Save current width
            self.sidebar.setFixedWidth(35)
            self.menu_bar.actions["toggle_sidebar"].setChecked(False)
        else:
            self.sidebar.setFixedWidth(self.sidebar_width)
            self.menu_bar.actions["toggle_sidebar"].setChecked(True)

    def toggle_statusbar_visibility(self):
        self.status_bar.setVisible(not self.status_bar.isVisible())
        # Sync the checkbox in the menu
        is_visible = self.status_bar.isVisible()
        self.menu_bar.actions["toggle_statusbar"].setChecked(is_visible)

    def handle_tab_bar_click(self, index):
        # If the sidebar is collapsed, expand it.
        if self.sidebar.width() <= 50:
            self.sidebar.setFixedWidth(self.sidebar_width)
        # If the sidebar is expanded and the current tab is clicked, collapse it.
        elif index == self.sidebar.tabs.currentIndex():
            self.toggle_sidebar_visibility()

    def set_theme(self, theme_name):
        theme = theme_name.lower()
        is_dark = (theme == "dark")

        # Block signals to prevent infinite loops
        self.sidebar.theme_combo.blockSignals(True)
        self.menu_bar.actions["dark_mode"].blockSignals(True)

        # Update UI state
        self.sidebar.theme_combo.setCurrentText(theme.capitalize())
        self.menu_bar.actions["dark_mode"].setChecked(is_dark)

        # Unblock signals
        self.sidebar.theme_combo.blockSignals(False)
        self.menu_bar.actions["dark_mode"].blockSignals(False)

        self.settings_model.update_theme(theme_name)
        self.settings_model.save(self.settings_manager)
        self.apply_theme()

    def set_dark_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.apply_dark()

    def apply_dark_theme(self):
        self.set_dark_theme()

    def apply_light_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.apply_light(self.sidebar)

    def load_settings(self):
        self.apply_settings_to_ui()

    def apply_settings_to_ui(self):
        self.apply_theme()

        font = QFont(self.settings_model.editor_font_family, self.settings_model.editor_font_size)
        self.sidebar.font_combo.setCurrentFont(font)
        self.sidebar.font_size_spinbox.setValue(self.settings_model.editor_font_size)

        self.apply_editor_font_size(self.settings_model.editor_font_size)
        self.apply_sidebar_width(self.settings_model.sidebar_width)
        self.apply_sidebar_font_size(self.settings_model.sidebar_font_size)

        self.sidebar.word_wrap_checkbox.setChecked(self.settings_model.word_wrap)
        self.apply_word_wrap(Qt.Checked if self.settings_model.word_wrap else Qt.Unchecked)

    def apply_theme(self):
        from view.theme_manager import ThemeManager

        ThemeManager.sync_ui(self.sidebar, self.menu_bar.actions, self.settings_model.theme)
        if self.settings_model.theme.lower() == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

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
        self.settings_model.update_editor_font_size(size)
        self.settings_model.save(self.settings_manager)
        self.apply_editor_font_size(size)

    def apply_editor_font_size(self, size):
        # Block signals from spinbox to prevent recursion
        self.sidebar.font_size_spinbox.blockSignals(True)
        self.sidebar.font_size_spinbox.setValue(size)
        self.sidebar.font_size_spinbox.blockSignals(False)

        # Apply font size to all tabs
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorArea):
                widget.setFontPointSize(size)

    def change_sidebar_width(self, delta):
        current_width = int(self.sidebar.sidebar_width_label.text())
        new_width = max(200, min(600, current_width + delta)) # Clamp between 200 and 600
        self.set_sidebar_width(new_width)

    def set_sidebar_width(self, width):
        self.sidebar_width = width
        self.settings_model.update_sidebar_width(width)
        self.settings_model.save(self.settings_manager)
        self.apply_sidebar_width(width)

    def apply_sidebar_width(self, width):
        self.sidebar.sidebar_width_label.setText(str(width))
        if self.sidebar.width() > 50:
            self.resizeDocks([self.sidebar], [width], Qt.Horizontal)

    def on_sidebar_manually_resized(self, width):
        # This slot is called when the user drags the sidebar edge.
        # It updates the internal state and the settings UI.
        self.set_sidebar_width(width)
        
    def change_sidebar_font_size(self, delta):
        current_size = int(self.sidebar.sidebar_font_size_label.text())
        new_size = max(8, min(20, current_size + delta)) # Clamp between 8 and 20
        self.set_sidebar_font_size(new_size)

    def set_sidebar_font_size(self, size):
        self.settings_model.update_sidebar_font_size(size)
        self.settings_model.save(self.settings_manager)
        self.apply_sidebar_font_size(size)

    def apply_sidebar_font_size(self, size):
        self.sidebar.widget().setStyleSheet(f"font-size: {size}pt;")
        self.sidebar.sidebar_font_size_label.setText(str(size))

    def set_word_wrap(self, state):
        enabled = state == Qt.Checked
        self.settings_model.update_word_wrap(enabled)
        self.settings_model.save(self.settings_manager)
        mode = QTextOption.WordWrap if enabled else QTextOption.NoWrap
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, EditorArea):
                widget.setWordWrapMode(mode)

    def print_file(self):
        editor = self.current_editor()
        if not editor: return
        printer = QPrinter(QPrinter.HighResolution)
        # You can add a print dialog here:
        # from PyQt5.QtPrintSupport import QPrintDialog
        # dialog = QPrintDialog(printer, self) ...
        editor.document().print_(printer)

    def export_to_pdf(self):
        """Exports the current content of the editor to a PDF file."""
        editor = self.current_editor()
        if not editor or not editor.toPlainText().strip():
            self.status_bar.showMessage("Nothing to export. The editor is empty.", 5000)
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)

        if file_path:
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            self.current_editor().document().print_(printer)
            self.status_bar.showMessage(f"Successfully exported to {os.path.basename(file_path)}", 5000)

    # --- Placeholder Methods for Menu Actions ---
    
    def find_next(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Find is only available in text editors.", 3000)
            return

        query = self.find_input.text()
        if not query:
            self.status_bar.showMessage("Enter search text before finding.", 3000)
            return

        found = SearchService.find_next(editor, query, self.find_case_sensitive_checkbox.isChecked())
        if not found:
            self.status_bar.showMessage(f"No matches found for '{query}'", 3000)

    def find_previous(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Find is only available in text editors.", 3000)
            return

        query = self.find_input.text()
        if not query:
            self.status_bar.showMessage("Enter search text before moving to the previous match.", 3000)
            return

        found = SearchService.find_previous(editor, query, self.find_case_sensitive_checkbox.isChecked())
        if not found:
            self.status_bar.showMessage(f"No matches found for '{query}'", 3000)

    def replace_text(self):
        self.find_bar.show()
        self.replace_input.show()
        self.replace_button.show()
        self.replace_and_find_button.show()
        self.replace_all_button.show()
        self.find_input.setFocus()
        self.find_input.selectAll()
        # Ensure the find bar is visible when replace_text is called
        if not self.find_bar.isVisible():
            self.find_bar.show()

    def update_window_title(self):
        widget = self.tab_widget.currentWidget()
        if not widget:
            self.setWindowTitle("StudyMate")
            return
        
        file_path = widget.file_path
        title = os.path.basename(file_path) if file_path else "Untitled"

        # Check if it's an editor and is modified
        if isinstance(widget, EditorArea) and widget.document().isModified():
            title += "*"
        
        self.setWindowTitle(f"{title} - StudyMate")

    def update_status_bar(self):
        editor = self.current_editor()
        if editor:
            self.status_bar.update_editor_info(editor)

    def reset_editor_zoom(self):
        # A bit of a workaround as there's no direct 'reset zoom'
        self.set_editor_font_size(self.settings_model.editor_font_size)

    def toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showMaximized()

    def toggle_dark_mode(self, checked):
        self.set_theme("dark" if checked else "light")

    def show_documentation(self):
        QMessageBox.information(self, "Documentation", "StudyMate Help:\n\n• File → New/Open/Save, multi-tab editor, find/replace (Ctrl+F)\n• PDF viewer with zoom & page navigation\n• AI Sidebar: Summarize, Key Points, Generate Mind Map (+ Export PNG)\n• Scheduler: add tasks, mark done (persisted)\n• Settings: theme, font, sidebar width\n\nDocs: README.md in repo root.")

    def check_for_updates(self):
        try:
            import requests
            r = requests.get("https://api.github.com/repos/smartnotes-app/smartnotes-application/releases/latest", timeout=5)
            if r.status_code == 200:
                tag = r.json().get("tag_name", "unknown")
                QMessageBox.information(self, "Updates", f"Latest release: {tag}\nYou are on v0.2.0.\nVisit GitHub to update if needed.")
            else:
                raise RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Updates", f"Could not check for updates:\n{e}\n\nVisit github.com to check manually.")
            self.status_bar.showMessage("Update check failed.", 4000)

    def send_feedback(self):
        QDesktopServices.openUrl(QUrl("https://github.com/smartnotes-application/issues/new"))
        self.status_bar.showMessage("Opened feedback page in browser.", 3000)

    def show_about_dialog(self):
        QMessageBox.about(self, "About StudyMate",
                          "StudyMate (SmartNotes) v0.2.0\n\nLightweight PyQt5 notes, PDF viewer, AI summarizer & scheduler.\n\nPython 3.11+ • PyQt5 • Hugging Face transformers\nLicensed MIT – see LICENSE file.\n© 2026 StudyMate contributors.")

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
            editor,
            query,
            replace_text,
            self.find_case_sensitive_checkbox.isChecked(),
        )

        self.status_bar.showMessage(
            "Replaced current selection." if replaced else "No matching selection to replace.",
            2000,
        )

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
            original_text,
            query,
            replace_text,
            self.find_case_sensitive_checkbox.isChecked(),
        )

        if replacements == 0:
            self.status_bar.showMessage(f"No occurrences of '{query}' found.", 3000)
            return

        editor.setPlainText(new_text)
        editor.document().setModified(True)
        self.status_bar.showMessage(f"Replaced {replacements} occurrences of '{query}'.", 3000)
