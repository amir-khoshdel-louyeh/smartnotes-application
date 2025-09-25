import os
import docx
import pypdf
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTabWidget
from PyQt5.QtPrintSupport import QPrinter
from view.editor_area import EditorArea
from PyQt5.QtGui import QFont, QTextOption

class FileHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget: QTabWidget = main_window.tab_widget
        self.status_bar = main_window.status_bar
        self.sidebar = main_window.sidebar
        self.settings = main_window.settings

    def new_file(self, is_initial_tab=False):
        """Prompts the user to create a new file, asking for name and location."""
        file_path = None
        if is_initial_tab:
            pass
        else:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self.main_window, "Create New File", "", "Text Files (*.txt);;Markdown Files (*.md *.markdown);;Python Files (*.py);;All Files (*)", options=options)
            if not file_path:
                return

        if file_path and self.is_file_open(file_path):
            return

        try:
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                self.sidebar.show_directory_in_explorer(file_path)
            self.create_new_tab(file_path)
        except Exception as e:
            self.status_bar.showMessage(f"Error creating file: {e}", 5000)

    def create_new_tab(self, file_path=None, content=""):
        """Creates a new tab with an EditorArea."""
        editor = EditorArea(file_path=file_path)
        editor.setText(content)
        
        font_family = self.settings.value("editorFontFamily", "Consolas")
        font_size = self.settings.value("editorFontSize", 11, type=int)
        editor.setFont(QFont(font_family, font_size))
        word_wrap = self.settings.value("wordWrap", "true", type=str) == "true"
        editor.setWordWrapMode(QTextOption.WordWrap if word_wrap else QTextOption.NoWrap)

        editor.document().modificationChanged.connect(lambda modified, ed=editor: self.main_window.on_modification_changed(ed, modified))
        editor.cursorPositionChanged.connect(self.main_window.update_status_bar)

        tab_name = os.path.basename(file_path) if file_path else "Untitled"
        index = self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setTabToolTip(index, file_path or "New unsaved file")
        self.tab_widget.setCurrentIndex(index)

        self.main_window.update_window_title()
        self.main_window.update_status_bar()
        return editor

    def open_file(self, file_path=None):
        if not file_path:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self.main_window, "Open File", "", "All Files (*);;Text Files (*.txt);;Markdown Files (*.md *.markdown);;Python Files (*.py);;PDF Files (*.pdf);;Word Documents (*.docx)", options=options)
        
        if file_path:
            if self.is_file_open(file_path):
                return
            self.load_file(file_path)

    def is_file_open(self, file_path):
        """Checks if a file is already open in a tab and focuses it if so."""
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor and editor.file_path == file_path:
                self.tab_widget.setCurrentIndex(i)
                return True
        return False

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
            readers = {
                '.txt': self._read_txt, '.md': self._read_txt, '.markdown': self._read_txt, '.py': self._read_txt,
                '.docx': self._read_docx,
                '.pdf': self._read_pdf,
            }
            reader_func = readers.get(extension.lower(), self._read_txt)
            content = reader_func(file_path)

            if self.tab_widget.count() == 1 and not self.main_window.current_editor().file_path and not self.main_window.current_editor().toPlainText():
                self.tab_widget.removeTab(0)

            self.create_new_tab(file_path, content)
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.sidebar.show_directory_in_explorer(file_path)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file", 5000)
            print(f"Error loading file: {e}")

    def close_current_file(self):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.close_tab(current_index)

    def close_tab(self, index):
        editor_widget = self.tab_widget.widget(index)
        if not editor_widget:
            return True

        if editor_widget.document().isModified():
            file_name = self.tab_widget.tabText(index).replace('*', '')
            reply = QMessageBox.question(self.main_window, 'Save Changes?', f"Do you want to save the changes you made to '{file_name}'?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if reply == QMessageBox.Save:
                if not self.save_file(index=index):
                    return False
            elif reply == QMessageBox.Cancel:
                return False

        self.tab_widget.removeTab(index)
        editor_widget.deleteLater()
        
        if self.tab_widget.count() == 0:
            self.new_file(is_initial_tab=True)
        return True

    def save_file(self, index=None):
        if index is None: index = self.tab_widget.currentIndex()
        editor = self.tab_widget.widget(index)
        if not editor: return False

        if editor.file_path:
            try:
                with open(editor.file_path, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                editor.document().setModified(False)
                if index == self.tab_widget.currentIndex():
                    self.status_bar.showMessage(f"Saved to {os.path.basename(editor.file_path)}", 3000)
                return True
            except Exception as e:
                self.status_bar.showMessage(f"Error saving file: {e}", 5000)
                return False
        else:
            return self.save_file_as(index=index)

    def save_file_as(self, index=None):
        if index is None: index = self.tab_widget.currentIndex()
        editor = self.tab_widget.widget(index)
        if not editor: return False

        current_name = os.path.basename(editor.file_path) if editor.file_path else ""
        file_path, _ = QFileDialog.getSaveFileName(self.main_window, "Save File As", current_name, "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)", options=QFileDialog.Options())
        
        if file_path:
            editor.file_path = file_path
            self.tab_widget.setTabText(index, os.path.basename(file_path))
            self.tab_widget.setTabToolTip(index, file_path)
            self.main_window.update_window_title()
            return self.save_file(index=index)
        return False