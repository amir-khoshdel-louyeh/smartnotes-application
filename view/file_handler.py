import os
import docx
import subprocess
import tempfile
import shutil
from odf import text, teletype
from odf.opendocument import load as load_odt
import pypdf
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTabWidget
from view.pdf_viewer import PdfViewer
from view.editor_area import EditorArea
from PyQt5.QtGui import QFont, QTextOption
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

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

    def _read_odt(self, file_path):
        doc = load_odt(file_path)
        all_paras = doc.getElementsByType(text.P)
        content = "\n".join(teletype.extractText(p) for p in all_paras)
        return content

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
                    # Convert ODT to PDF and open in viewer
                    pdf_path = self._convert_odt_to_pdf(file_path)
                    if pdf_path:
                        self.create_new_pdf_tab(pdf_path, is_temporary=True)
                elif clicked_button == open_externally_button: # Open with LibreOffice etc.
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                else: # User cancelled
                    return
                return # ODT handling is complete

            _, extension = os.path.splitext(file_path)
            readers = {
                '.txt': self._read_txt, '.md': self._read_txt, '.markdown': self._read_txt, '.py': self._read_txt,
                '.docx': self._read_docx, 
                '.odt': self._read_odt,
            }
            reader_func = readers.get(extension.lower(), self._read_txt)
            content = reader_func(file_path) # This will now only be called for .txt, .docx etc.

            self.create_new_tab(file_path, content)
            self.status_bar.showMessage(f"Successfully loaded {os.path.basename(file_path)}", 5000)
            self.sidebar.show_directory_in_explorer(file_path)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file", 5000)
            print(f"Error loading file: {e}")

    def _convert_odt_to_pdf(self, odt_path):
        """Converts an ODT file to PDF using LibreOffice and returns the new PDF path."""
        self.status_bar.showMessage("Converting ODT to PDF...", 5000)
        try:
            temp_dir = tempfile.mkdtemp()
            subprocess.run(
                ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', temp_dir, odt_path],
                check=True,
                capture_output=True,
                text=True
            )
            base_name = os.path.splitext(os.path.basename(odt_path))[0]
            pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
            if os.path.exists(pdf_path):
                self.status_bar.showMessage("Conversion successful.", 3000)
                return pdf_path
            else:
                raise FileNotFoundError("Converted PDF not found.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_details = e.stderr if isinstance(e, subprocess.CalledProcessError) else str(e)
            error_message = f"Failed to convert ODT to PDF. Please ensure LibreOffice is installed and in your system's PATH.\n\nError details:\n{error_details}"
            QMessageBox.critical(self.main_window, "Conversion Error", error_message)
            return None
        except Exception as e:
            QMessageBox.critical(self.main_window, "Conversion Error", f"An unexpected error occurred during conversion: {e}")

    def create_new_pdf_tab(self, file_path, is_temporary=False):
        """Creates a new tab with a PdfViewer."""
        viewer = PdfViewer(file_path=file_path)
        viewer.is_temporary_file = is_temporary
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