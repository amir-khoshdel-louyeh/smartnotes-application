import os
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTabWidget
from view.pdf_viewer import PdfViewer
from view.editor_area import EditorArea
from view.file_service import FileService
from view.document_model import DocumentModel
from PyQt5.QtGui import QFont, QTextOption
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

class FileHandler:
    def __init__(self, main_window, file_service: FileService | None = None):
        self.main_window = main_window
        self.tab_widget: QTabWidget = main_window.tab_widget
        self.status_bar = main_window.status_bar
        self.sidebar = main_window.sidebar
        self.settings = main_window.settings
        self.file_service = file_service or FileService()

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

        editor.document_model = DocumentModel(file_path=file_path)

        tab_name = os.path.basename(file_path) if file_path else editor.document_model.display_name
        index = self.tab_widget.addTab(editor, tab_name)
        self.tab_widget.setTabToolTip(index, file_path or "New unsaved file")
        self.tab_widget.setCurrentIndex(index)

        self.main_window.update_window_title()
        self.main_window.update_status_bar()
        return editor

    def open_file(self, file_path=None):
        if not file_path:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getOpenFileName(self.main_window, "Open File", "", "All Files (*);;Text Files (*.txt);;Markdown Files (*.md *.markdown);;Python Files (*.py);;PDF Files (*.pdf);;Word Documents (*.docx);;OpenDocument Text (*.odt)", options=options)
        
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

    def load_file(self, file_path):
        try:
            # For PDF files, ask the user how they want to open it.
            if file_path.lower().endswith('.pdf'):
                msg_box = QMessageBox(self.main_window)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setText(f"How would you like to open this PDF?")
                msg_box.setInformativeText(os.path.basename(file_path))
                msg_box.setWindowTitle("Open PDF")
                
                open_in_app_button = msg_box.addButton("Open in App", QMessageBox.AcceptRole)
                open_externally_button = msg_box.addButton("Use Default PDF Reader", QMessageBox.ApplyRole)
                msg_box.addButton(QMessageBox.Cancel)
                
                msg_box.exec_()
                clicked_button = msg_box.clickedButton()

                if clicked_button == open_in_app_button:
                    self.create_new_pdf_tab(file_path)
                    self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
                elif clicked_button == open_externally_button:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                return
            
            # For ODT files, also ask the user how to open it.
            if file_path.lower().endswith('.odt'):
                msg_box = QMessageBox(self.main_window)
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setText("How would you like to open this ODT file?")
                msg_box.setInformativeText("Opening in the app will convert it to a PDF for viewing.")
                msg_box.setWindowTitle("Open ODT")
                
                open_in_app_button = msg_box.addButton("Open in App", QMessageBox.AcceptRole)
                open_externally_button = msg_box.addButton("Use Default App", QMessageBox.ApplyRole)
                msg_box.addButton(QMessageBox.Cancel)
                
                msg_box.exec_()
                clicked_button = msg_box.clickedButton()

                if clicked_button == open_in_app_button: # Open as PDF
                    pdf_path = self.file_service.convert_odt_to_pdf(file_path)
                    if pdf_path:
                        self.create_new_pdf_tab(pdf_path, is_temporary=True)
                elif clicked_button == open_externally_button: # Open with LibreOffice etc.
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                else: # User cancelled
                    return
                return # ODT handling is complete

            extension = os.path.splitext(file_path)[1].lower()
            if extension in ['.txt', '.md', '.markdown', '.py']:
                content = self.file_service.read_text_file(file_path)
            elif extension == '.docx':
                content = self.file_service.read_docx(file_path)
            else:
                content = self.file_service.read_text_file(file_path)

            self.create_new_tab(file_path, content)
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.sidebar.show_directory_in_explorer(file_path)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file", 5000)
            print(f"Error loading file: {e}")


    def create_new_pdf_tab(self, file_path, is_temporary=False):
        """Creates a new tab with a PdfViewer."""
        viewer = PdfViewer(file_path=file_path)
        viewer.is_temporary_file = is_temporary
        viewer.document_model = DocumentModel(file_path=file_path, is_temporary=is_temporary, is_pdf=True)
        tab_name = os.path.basename(file_path)
        index = self.tab_widget.addTab(viewer, tab_name)
        self.tab_widget.setTabToolTip(index, file_path)
        self.tab_widget.setCurrentIndex(index)
        self.main_window.update_window_title()

    def close_current_file(self):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.close_tab(current_index)

    def close_all_files(self):
        """Closes all open tabs, prompting for unsaved changes for each."""
        # Iterate backwards to avoid index shifting issues as tabs are removed.
        for i in range(self.tab_widget.count() - 1, -1, -1):
            # close_tab returns False if the user cancels the close operation
            if not self.close_tab(i):
                # If user cancels, stop closing further tabs
                break

    def close_tab(self, index):
        editor_widget = self.tab_widget.widget(index)
        if not editor_widget:
            return True

        # Clean up temporary PDF files from ODT conversions
        if isinstance(editor_widget, PdfViewer) and editor_widget.is_temporary_file:
            temp_dir = os.path.dirname(editor_widget.file_path)
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Check for modifications only if it's an editor
        if isinstance(editor_widget, EditorArea) and editor_widget.document().isModified():
            file_name = self.tab_widget.tabText(index).replace('*', '')
            reply = QMessageBox.question(self.main_window, 'Save Changes?', f"Do you want to save the changes you made to '{file_name}'?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if reply == QMessageBox.Save:
                if not self.save_file(index=index):
                    return False
            elif reply == QMessageBox.Cancel:
                return False

        self.tab_widget.removeTab(index)
        editor_widget.deleteLater()
        
        # If the last tab was closed, open a new empty one
        if self.tab_widget.count() == 0:
            self.new_file(is_initial_tab=True)

        return True

    def save_file(self, index=None):
        if index is None: index = self.tab_widget.currentIndex()
        editor = self.tab_widget.widget(index)
        if not editor: return False

        if editor.file_path:
            try:
                self.file_service.save_text_file(editor.file_path, editor.toPlainText())
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
            if hasattr(editor, 'document_model'):
                editor.document_model.update_path(file_path)
            self.tab_widget.setTabText(index, os.path.basename(file_path))
            self.tab_widget.setTabToolTip(index, file_path)
            self.main_window.update_window_title()
            return self.save_file(index=index)
        return False