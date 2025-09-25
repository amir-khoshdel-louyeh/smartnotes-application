from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QAction, QTextEdit, QWidget, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QVBoxLayout
from PyQt5.QtCore import Qt, QSettings, QThreadPool, QTimer
from PyQt5.QtGui import QFont, QTextOption, QDesktopServices, QTextDocument, QTextCursor, QKeySequence
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QUrl
from view.menu_bar import MenuBar
from view.side_bar import SideBar
from view.editor_area import EditorArea
from view.status_bar import StatusBar
from services.summarizer import SummarizationWorker, PreloadWorker
from services.key_points_extractor import KeyPointsWorker

import os
import sys
import docx
import pypdf

class MainWindow(QMainWindow):
    def __init__(self):
        self.settings = QSettings("StudyMate", "StudyMate") # OrganizationName, ApplicationName
        super().__init__()
        self.setWindowTitle("StudyMate")
        self.setGeometry(100, 100, 1200, 800)
        self.current_file_path = None
        self.sidebar_width = 300 # Default/initial width
        self.thread_pool = QThreadPool()

        # Menu Bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Central Editor
        self.editor = EditorArea()

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
        main_layout.addWidget(self.editor)
        
        # Side Bar
        self.sidebar = SideBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)

        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Load settings
        self.load_settings()

        # Connect find bar signals
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

    def preload_models(self):
        self.thread_pool.start(PreloadWorker())

    def closeEvent(self, event):
        # Save settings before closing
        self.settings.sync()
        event.accept()

    def connect_signals(self):
        # File Menu
        self.menu_bar.actions["new"].triggered.connect(self.new_file)
        self.menu_bar.actions["open"].triggered.connect(self.open_file)
        self.menu_bar.actions["save"].triggered.connect(self.save_file)
        self.menu_bar.actions["save_as"].triggered.connect(self.save_file_as)
        self.menu_bar.actions["print"].triggered.connect(self.print_file)
        self.menu_bar.actions["export_pdf"].triggered.connect(self.export_to_pdf)
        self.menu_bar.actions["close"].triggered.connect(self.close_file)
        self.menu_bar.actions["exit"].triggered.connect(self.close)

        # Edit Menu
        self.menu_bar.undo_action.triggered.connect(self.editor.undo)
        self.menu_bar.redo_action.triggered.connect(self.editor.redo)
        self.menu_bar.cut_action.triggered.connect(self.editor.cut)
        self.menu_bar.copy_action.triggered.connect(self.editor.copy)
        self.menu_bar.paste_action.triggered.connect(self.editor.paste)
        # For delete, we can use the editor's delete function directly
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Delete)
        delete_action.triggered.connect(self.editor.textCursor().deleteChar)
        self.addAction(delete_action) # Add as a top-level action to catch the shortcut
        self.menu_bar.actions["select_all"].triggered.connect(self.editor.selectAll)
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
        self.sidebar.suggest_schedule_button.clicked.connect(self.suggest_study_plan)
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
        self.sidebar.toggle_sidebar_button_scheduler.clicked.connect(self.toggle_sidebar_visibility)
        self.sidebar.tabs.tabBarClicked.connect(self.handle_tab_bar_click)
        # Explore Tab
        # The buttons are now connected inside side_bar.py to self.parent() which is this MainWindow instance
        self.sidebar.explore_view.doubleClicked.connect(self.on_explore_file_selected)

    def open_external_link(self, url_string):
        QDesktopServices.openUrl(QUrl(url_string))

    def new_file(self):
        """Prompts the user to create a new file, asking for name and location."""
        options = QFileDialog.Options()
        # Added Markdown files to the save dialog filter
        file_path, selected_filter = QFileDialog.getSaveFileName(self, "Create New File", "", "Text Files (*.txt);;Markdown Files (*.md *.markdown);;Python Files (*.py);;All Files (*)", options=options)

        if file_path:
            # Ensure correct extension if none is provided and it's the selected filter
            if not os.path.splitext(file_path)[1]:
                if "(*.txt)" in selected_filter:
                    file_path += '.txt'
                elif "(*.md *.markdown)" in selected_filter:
                    file_path += '.md'
                elif "(*.py)" in selected_filter:
                    file_path += '.py'

            self.editor.clear()
            self.current_file_path = file_path
            try:
                # Create an empty file so it exists on the filesystem
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass  # Just create the file
                self.setWindowTitle(f"StudyMate - {os.path.basename(file_path)}")
                # Update the explorer to show the new file's directory
                self.sidebar.show_directory_in_explorer(file_path)
            except Exception as e:
                self.status_bar.showMessage(f"Error creating file: {e}", 5000)
                self.current_file_path = None

    def on_explore_file_selected(self, index):
        file_path = self.sidebar.file_model.filePath(index)
        # Check if it's a file, not a directory
        if os.path.isfile(file_path):
            self.load_file(file_path)

    def run_summarization(self):
        text_to_summarize = self.editor.toPlainText()
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
        text_to_analyze = self.editor.toPlainText()
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

    def open_file(self):
        options = QFileDialog.Options()
        # Added Markdown files to the open dialog filter
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt);;Markdown Files (*.md *.markdown);;Python Files (*.py);;PDF Files (*.pdf);;Word Documents (*.docx)", options=options)
        if file_path:
            self.load_file(file_path)

    def _read_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_docx(self, file_path):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _read_pdf(self, file_path):
        content = ""
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                content += page.extract_text() + "\n"
        return content

    def load_file(self, file_path):
        try:
            _, extension = os.path.splitext(file_path)
            ext_lower = extension.lower()

            readers = {
                '.txt': self._read_txt,
                '.docx': self._read_docx,
                '.md': self._read_txt, # Treat markdown as plain text for now
                '.markdown': self._read_txt, # Treat markdown as plain text for now
                '.py': self._read_txt, # Treat python files as plain text
                '.pdf': self._read_pdf,
            }

            # Default to reading as a text file if the extension is not in the readers dict
            reader_func = readers.get(ext_lower, self._read_txt)
            content = reader_func(file_path)

            self.editor.setText(content)
            self.setWindowTitle(f"StudyMate - {os.path.basename(file_path)}")
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.current_file_path = file_path
            # Update the explorer to show the opened file's directory
            self.sidebar.show_directory_in_explorer(file_path)
        except Exception as e:
            self.editor.setText(f"Error loading file: {file_path}\n\n{str(e)}")
            self.status_bar.showMessage(f"Error loading file", 5000)

    def close_file(self):
        # In a more complex app, you'd check for unsaved changes here.
        self.editor.clear()
        self.current_file_path = None
        self.setWindowTitle("StudyMate")

    def editor_zoom_in(self):
        self.editor.zoomIn()
        current_size = self.editor.font().pointSize()
        self.set_editor_font_size(current_size)

    def editor_zoom_out(self):
        self.editor.zoomOut()
        current_size = self.editor.font().pointSize()
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
        self.editor.setFont(font)
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
        current_size = self.editor.font().pointSize()
        self.editor.setFont(QFont(font.family(), current_size))
        self.settings.setValue("editorFontFamily", font.family())

    def set_editor_font_size(self, size):
        # Block signals from spinbox to prevent recursion if this method is called by spinbox valueChanged
        self.sidebar.font_size_spinbox.blockSignals(True)
        self.sidebar.font_size_spinbox.setValue(size)
        self.sidebar.font_size_spinbox.blockSignals(False)

        # Set editor font size
        self.editor.setFontPointSize(size)
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
        self.editor.setWordWrapMode(mode)
        self.settings.setValue("wordWrap", "true" if state == Qt.Checked else "false")

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.status_bar.showMessage(f"Saved to {os.path.basename(self.current_file_path)}", 3000)
            except Exception as e:
                self.status_bar.showMessage(f"Error saving file: {e}", 5000)
        else:
            self.save_file_as()

    def save_file_as(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            # Ensure .txt extension if none is provided
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            
            self.current_file_path = file_path
            self.save_file()

    def print_file(self):
        printer = QPrinter(QPrinter.HighResolution)
        # You can add a print dialog here:
        # from PyQt5.QtPrintSupport import QPrintDialog
        # dialog = QPrintDialog(printer, self) ...
        self.editor.document().print_(printer)

    def export_to_pdf(self):
        """Exports the current content of the editor to a PDF file."""
        if not self.editor.toPlainText().strip():
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
            self.editor.document().print_(printer)
            self.status_bar.showMessage(f"Successfully exported to {os.path.basename(file_path)}", 5000)

    # --- Placeholder Methods for Menu Actions ---

    def find_next(self):
        query = self.find_input.text()
        if not query:
            return

        flags = QTextDocument.FindFlags()
        if self.find_case_sensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        found = self.editor.find(query, flags)
        if not found:
            # Wrap around to the beginning
            self.editor.moveCursor(QTextCursor.Start)
            self.editor.find(query, flags)

    def find_previous(self):
        query = self.find_input.text()
        if not query:
            return

        flags = QTextDocument.FindFlags() | QTextDocument.FindBackward
        if self.find_case_sensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively

        found = self.editor.find(query, flags)
        if not found:
            # Wrap around to the end
            self.editor.moveCursor(QTextCursor.End)
            self.editor.find(query, flags)

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
        query = self.find_input.text()
        if not query or not self.editor.textCursor().hasSelection():
            return

        # Check if the selected text matches the find query
        cursor = self.editor.textCursor()
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
        query = self.find_input.text()
        replace_text = self.replace_input.text()
        if not query:
            return

        original_text = self.editor.toPlainText()
        flags = Qt.CaseInsensitive if not self.find_case_sensitive_checkbox.isChecked() else Qt.CaseSensitive
        new_text = original_text.replace(query, replace_text)

        if original_text != new_text:
            self.editor.setPlainText(new_text)
            self.status_bar.showMessage(f"Replaced all occurrences of '{query}'.", 3000)
