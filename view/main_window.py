from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QAction, QTextEdit, QWidget, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QVBoxLayout, QTabWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QSettings, QThreadPool
from PyQt5.QtGui import QFont, QTextOption, QDesktopServices, QTextDocument, QTextCursor, QKeySequence
import re
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QUrl
from view.menu_bar import MenuBar
from view.side_bar import SideBar
from view.editor_area import EditorArea
from view.file_handler import FileHandler
from view.status_bar import StatusBar
from services.summarizer import SummarizationWorker, PreloadWorker
from services.key_points_extractor import KeyPointsWorker
import os

class MainWindow(QMainWindow):
    def __init__(self):
        self.settings = QSettings("StudyMate", "StudyMate") # OrganizationName, ApplicationName
        super().__init__()
        self.setWindowTitle("StudyMate")
        self.setGeometry(100, 100, 1400, 900)
        self.sidebar_width = 300 # Default/initial width
        self.thread_pool = QThreadPool()

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

        # Handlers (must be initialized after the widgets they handle)
        self.file_handler = FileHandler(self)
        
        # Connect signals that depend on handlers
        self.tab_widget.tabCloseRequested.connect(self.file_handler.close_tab)

        # Load settings
        self.load_settings()

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
        # Use the existing close_all_files logic.
        # This will prompt to save for each unsaved tab.
        self.file_handler.close_all_files()
        
        # After attempting to close all, check if any tabs remain.
        # A tab might remain if the user cancels a "Save" dialog.
        if self.tab_widget.count() > 1 or (self.tab_widget.count() == 1 and self.tab_widget.widget(0).file_path is not None):
            event.ignore() # User cancelled, so don't close the window.
        else:
            self.settings.sync() # All tabs closed, so save settings and exit.
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
        QDesktopServices.openUrl(QUrl(url_string))

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

    def suggest_study_plan(self):
        # Placeholder for adaptive scheduler logic
        self.sidebar.schedule_output.setPlainText("Feature coming soon!\n\nThis will analyze your notes and suggest a study plan based on topics and your activity.")

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

        if is_dark:
            self.set_dark_theme()
        else:
            self.set_light_theme()

    def set_dark_theme(self):
        QApplication.instance().setProperty("theme", "dark")
        QApplication.instance().setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: "Segoe UI", "Cantarell", "sans-serif";
            font-size: 10pt;
        }
        QTextEdit {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3c3c3c;
            font-family: "Consolas", "Monaco", "monospace";
            font-size: 11pt;
        }
        QDockWidget {
            background-color: #252526;
            color: #cccccc;
        }
        QDockWidget::title {
            text-align: left;
            background: #3c3c3c;
            padding-left: 5px;
        }
        QMenuBar {
            background-color: #3c3c3c;
            color: #cccccc;
        }
        QMenuBar::item:selected {
            background-color: #505050;
        }
        QMenu {
            background-color: #252526;
            border: 1px solid #3c3c3c;
        }
        QMenu::item:selected {
            background-color: #094771;
            color: #ffffff;
        }
        QStatusBar {
            background-color: #007acc;
            color: #ffffff;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 2px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QPushButton:pressed {
            background-color: #5c5c5c;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #aaaaaa;
            padding: 8px;
        }
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #3c3c3c;
        }
        QScrollBar:vertical {
            border: none;
            background: #252526;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #4a4a4a;
            min-height: 20px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #252526;
            height: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: #4a4a4a;
            min-width: 20px;
        }
        """)
        self.settings.setValue("theme", "dark")

    def set_light_theme(self):
        QApplication.instance().setStyleSheet("")  # Reset to default os style
        self.settings.setValue("theme", "light")
        QApplication.instance().setProperty("theme", "light")
        self.sidebar.setStyleSheet("") # Reset sidebar font

    def load_settings(self):
        # Load and apply theme
        theme = self.settings.value("theme", "light")
        self.set_theme(theme)

        # Load and apply font settings
        font_family = self.settings.value("editorFontFamily", "Consolas")
        font_size = self.settings.value("editorFontSize", 11, type=int)
        font = QFont(font_family, font_size)
        # The font is now applied to each new tab in create_new_tab
        # and to existing tabs in set_editor_font/set_editor_font_size
        self.sidebar.font_combo.setCurrentFont(font)
        self.sidebar.font_size_spinbox.setValue(font_size)

        # Load and apply sidebar settings
        self.set_sidebar_width(self.settings.value("sidebarWidth", 300, type=int))
        self.set_sidebar_font_size(self.settings.value("sidebarFontSize", 10, type=int))

        # Load and apply word wrap
        word_wrap = self.settings.value("wordWrap", "true", type=str) == "true"
        self.sidebar.word_wrap_checkbox.setChecked(word_wrap)
        self.set_word_wrap(Qt.Checked if word_wrap else Qt.Unchecked)

    def set_editor_font(self, font):
        editor = self.current_editor()
        if not editor: return
        current_size = editor.font().pointSize()
        new_font = QFont(font.family(), current_size)
        # Apply to all other tabs as well
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).setFont(new_font)
        self.settings.setValue("editorFontFamily", font.family())

    def set_editor_font_size(self, size):
        # Block signals from spinbox to prevent recursion
        self.sidebar.font_size_spinbox.blockSignals(True)
        self.sidebar.font_size_spinbox.setValue(size)
        self.sidebar.font_size_spinbox.blockSignals(False)

        # Apply to all tabs
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).setFontPointSize(size)
        self.settings.setValue("editorFontSize", size)

    def change_sidebar_width(self, delta):
        current_width = int(self.sidebar.sidebar_width_label.text())
        new_width = max(200, min(600, current_width + delta)) # Clamp between 200 and 600
        self.set_sidebar_width(new_width)

    def set_sidebar_width(self, width):
        self.sidebar_width = width
        self.settings.setValue("sidebarWidth", width)
        self.sidebar.sidebar_width_label.setText(str(width))

        # Use resizeDocks to programmatically resize without locking it.
        # This preserves the user's ability to resize with the mouse.
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
        self.sidebar.widget().setStyleSheet(f"font-size: {size}pt;")
        self.settings.setValue("sidebarFontSize", size)
        self.sidebar.sidebar_font_size_label.setText(str(size))

    def set_word_wrap(self, state):
        mode = QTextOption.WordWrap if state == Qt.Checked else QTextOption.NoWrap
        # Apply to all tabs
        for i in range(self.tab_widget.count()):
            self.tab_widget.widget(i).setWordWrapMode(mode)
        self.settings.setValue("wordWrap", "true" if state == Qt.Checked else "false")

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
            return

        flags = QTextDocument.FindFlags()
        if self.find_case_sensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        found = editor.find(query, flags)
        if not found:
            # Wrap around to the beginning
            editor.moveCursor(QTextCursor.Start)
            editor.find(query, flags)

    def find_previous(self):
        editor = self.current_editor()
        if not editor:
            self.status_bar.showMessage("Find is only available in text editors.", 3000)
            return
        query = self.find_input.text()
        if not query:
            return

        flags = QTextDocument.FindFlags() | QTextDocument.FindBackward
        if self.find_case_sensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        found = editor.find(query, flags)
        if not found:
            # Wrap around to the end
            editor.moveCursor(QTextCursor.End)
            editor.find(query, flags)

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
        self.set_editor_font_size(self.settings.value("editorFontSize", 11, type=int))

    def toggle_fullscreen(self, checked):
        if checked:
            self.showFullScreen()
        else:
            self.showMaximized()

    def toggle_dark_mode(self, checked):
        self.set_theme("dark" if checked else "light")

    def show_documentation(self):
        self.status_bar.showMessage("Show documentation action triggered (not implemented).", 3000)

    def check_for_updates(self):
        self.status_bar.showMessage("Check for updates action triggered (not implemented).", 3000)

    def send_feedback(self):
        self.status_bar.showMessage("Send feedback action triggered (not implemented).", 3000)

    def show_about_dialog(self):
        self.status_bar.showMessage("Show about dialog action triggered (not implemented).", 3000)

    def replace_current(self):
        editor = self.current_editor()
        if not editor: return
        query = self.find_input.text()
        if not query or not editor.textCursor().hasSelection():
            return

        # Check if the selected text matches the find query
        cursor = editor.textCursor()
        selected_text = cursor.selectedText()
        
        is_case_sensitive = self.find_case_sensitive_checkbox.isChecked()
        query_matches = selected_text == query if is_case_sensitive else selected_text.lower() == query.lower()

        if query_matches:
            replace_text = self.replace_input.text()
            cursor.insertText(replace_text)

    def replace_and_find(self):
        self.replace_current()
        self.find_next()

    def replace_all(self):
        editor = self.current_editor()
        if not editor: return
        query = self.find_input.text()
        replace_text = self.replace_input.text()
        if not query:
            return

        original_text = editor.toPlainText()
        pattern = re.escape(query)
        flags = re.IGNORECASE if not self.find_case_sensitive_checkbox.isChecked() else 0
        new_text = re.sub(pattern, replace_text, original_text, flags=flags)

        if original_text != new_text:
            editor.setPlainText(new_text)
            self.status_bar.showMessage(f"Replaced all occurrences of '{query}'.", 3000)
