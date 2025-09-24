from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QAction, QTextEdit
from PyQt5.QtCore import Qt, QSettings, QThreadPool, QTimer
from PyQt5.QtGui import QFont, QTextOption
from .menu_bar import MenuBar
from .side_bar import SideBar
from .editor_area import EditorArea
from .status_bar import StatusBar
from services.summarizer import SummarizationWorker
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
        self.setCentralWidget(self.editor)

        # Side Bar
        self.sidebar = SideBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)

        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Load settings
        self.load_settings()

        # Connect signals
        self.connect_signals()

    def closeEvent(self, event):
        # Save settings before closing
        self.settings.sync()
        event.accept()

    def connect_signals(self):
        # File Menu
        self.menu_bar.open_action.triggered.connect(self.open_file)
        self.menu_bar.save_action.triggered.connect(self.save_file)
        self.menu_bar.save_as_action.triggered.connect(self.save_file_as)
        self.menu_bar.exit_action.triggered.connect(self.close)

        # Edit Menu
        self.menu_bar.undo_action.triggered.connect(self.editor.undo)
        self.menu_bar.redo_action.triggered.connect(self.editor.redo)
        self.menu_bar.cut_action.triggered.connect(self.editor.cut)
        self.menu_bar.copy_action.triggered.connect(self.editor.copy)
        self.menu_bar.paste_action.triggered.connect(self.editor.paste)

        # View Menu
        self.menu_bar.toggle_sidebar_action.triggered.connect(self.toggle_sidebar_visibility)

        # --- Sidebar signals ---
        # AI Tab
        self.sidebar.summarize_button.clicked.connect(self.run_summarization)
        self.sidebar.key_points_button.clicked.connect(self.run_key_points_extraction)
        # Scheduler Tab
        self.sidebar.suggest_schedule_button.clicked.connect(self.suggest_study_plan)
        # Settings Tab
        self.sidebar.theme_combo.currentTextChanged.connect(self.set_theme)
        self.sidebar.font_combo.currentFontChanged.connect(self.set_editor_font)
        self.sidebar.font_size_spinbox.valueChanged.connect(self.set_editor_font_size)
        self.sidebar.word_wrap_checkbox.stateChanged.connect(self.set_word_wrap)
        self.sidebar.toggle_sidebar_button_scheduler.clicked.connect(self.toggle_sidebar_visibility)
        self.sidebar.toggle_sidebar_button.clicked.connect(self.toggle_sidebar_visibility)
        self.sidebar.tabs.tabBarClicked.connect(self.handle_tab_bar_click)

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
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Documents (*.docx)", options=options)
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
                '.pdf': self._read_pdf,
            }

            reader_func = readers.get(ext_lower)
            content = reader_func(file_path) if reader_func else f"Unsupported file type: {extension}"

            self.editor.setText(content)
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.current_file_path = file_path
        except Exception as e:
            self.editor.setText(f"Error loading file: {file_path}\n\n{str(e)}")
            self.status_bar.showMessage(f"Error loading file", 5000)

    def toggle_sidebar_visibility(self):
        # A width of 0 would hide the dock widget completely.
        # A small width will hide the content but keep the tab bar visible.
        if self.sidebar.width() > 50:
            self.sidebar_width = self.sidebar.width() # Save current width
            self.sidebar.setFixedWidth(35)
        else:
            self.sidebar.setFixedWidth(self.sidebar_width)

    def handle_tab_bar_click(self, index):
        # If the sidebar is collapsed, expand it.
        if self.sidebar.width() <= 50:
            self.sidebar.setFixedWidth(self.sidebar_width)
        # If the sidebar is expanded and the current tab is clicked, collapse it.
        elif index == self.sidebar.tabs.currentIndex():
            self.toggle_sidebar_visibility()

    def set_theme(self, theme_name):
        if theme_name.lower() == "dark":
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

    def load_settings(self):
        # Load and apply theme
        theme = self.settings.value("theme", "light")
        self.sidebar.theme_combo.setCurrentText(theme.capitalize())
        if theme == "dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()

        # Load and apply font settings
        font_family = self.settings.value("editorFontFamily", "Consolas")
        font_size = self.settings.value("editorFontSize", 11, type=int)
        font = QFont(font_family, font_size)
        self.editor.setFont(font)
        self.sidebar.font_combo.setCurrentFont(font)
        self.sidebar.font_size_spinbox.setValue(font_size)

        # Load and apply word wrap
        word_wrap = self.settings.value("wordWrap", "true", type=str) == "true"
        self.sidebar.word_wrap_checkbox.setChecked(word_wrap)
        self.set_word_wrap(Qt.Checked if word_wrap else Qt.Unchecked)

    def set_editor_font(self, font):
        current_size = self.editor.font().pointSize()
        self.editor.setFont(QFont(font.family(), current_size))
        self.settings.setValue("editorFontFamily", font.family())

    def set_editor_font_size(self, size):
        self.editor.setFontPointSize(size)
        self.settings.setValue("editorFontSize", size)

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
