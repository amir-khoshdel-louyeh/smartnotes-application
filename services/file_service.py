import os
import subprocess
import tempfile


class FileService:
    """Encapsulates file I/O and conversion logic for the app."""

    def _reader_registry(self) -> dict[str, callable]:
        return {
            '.txt': self.read_text_file,
            '.md': self.read_text_file,
            '.markdown': self.read_text_file,
            '.py': self.read_text_file,
            '.docx': self.read_docx,
            '.odt': self.read_odt,
            '.pdf': self.read_pdf,
        }

    def read_file(self, file_path: str) -> str:
        extension = os.path.splitext(file_path)[1].lower()
        reader = self._reader_registry().get(extension, self.read_text_file)
        return reader(file_path)

    def read_text_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def read_docx(self, file_path: str) -> str:
        import docx
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    def read_odt(self, file_path: str) -> str:
        from odf import text, teletype
        from odf.opendocument import load as load_odt

        document = load_odt(file_path)
        all_paras = document.getElementsByType(text.P)
        return "\n".join(teletype.extractText(p) for p in all_paras)

    def read_pdf(self, file_path: str) -> str:
        import pypdf

        content = []
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                content.append(page.extract_text() or "")
        return "\n".join(content)

    def save_text_file(self, file_path: str, content: str) -> None:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def convert_odt_to_pdf(self, odt_path: str) -> str | None:
        temp_dir = tempfile.mkdtemp()
        subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', temp_dir, odt_path],
            check=True,
            capture_output=True,
            text=True,
        )
        base_name = os.path.splitext(os.path.basename(odt_path))[0]
        pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
        return pdf_path if os.path.exists(pdf_path) else None

    def supported_text_extensions(self) -> list[str]:
        return list(self._reader_registry().keys())

    def is_text_extension(self, file_path: str) -> bool:
        return os.path.splitext(file_path)[1].lower() in self.supported_text_extensions()
