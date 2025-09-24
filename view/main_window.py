from PyQt5.QtWidgets import QMainWindow, QFileDialog, QApplication, QAction
from PyQt5.QtCore import Qt, QSettings
from .menu_bar import MenuBar
from .side_bar import SideBar
from .editor_area import EditorArea
from .status_bar import StatusBar

import os
import docx
import PyPDF2

class MainWindow(QMainWindow):
    def __init__(self):
        self.settings = QSettings("StudyMate", "StudyMate") # OrganizationName, ApplicationName
        super().__init__()
        self.setWindowTitle("StudyMate")
        self.setGeometry(100, 100, 1200, 800)
        self.current_file_path = None

        # Menu Bar
        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Central Editor
        self.editor = EditorArea()
        self.setCentralWidget(self.editor)

        # Side Bar
        self.sidebar = SideBar(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)

        # Load theme
        self.load_theme()

        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

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

        # Sidebar signals
        self.sidebar.theme_button.clicked.connect(self.toggle_theme)


    def open_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt);;PDF Files (*.pdf);;Word Documents (*.docx)", options=options)
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            _, extension = os.path.splitext(file_path)
            content = ""
            if extension.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif extension.lower() == '.docx':
                doc = docx.Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            elif extension.lower() == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
            
            self.editor.setText(content)
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.current_file_path = file_path
        except Exception as e:
            self.editor.setText(f"Error loading file: {file_path}\n\n{str(e)}")
            self.status_bar.showMessage(f"Error loading file", 5000)

    def toggle_theme(self):
        if QApplication.instance().property("theme") == "light":
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
        QApplication.instance().setProperty("theme", "light")
        QApplication.instance().setStyleSheet("")  # Reset to default os style
        self.settings.setValue("theme", "light")

    def load_theme(self):
        theme = self.settings.value("theme", "light")
        if theme == "dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()

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
