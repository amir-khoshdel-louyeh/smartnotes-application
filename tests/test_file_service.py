import os
import tempfile
import unittest

from services.file_service import FileService


class TestFileService(unittest.TestCase):
    def setUp(self):
        self.service = FileService()

    def test_read_and_save_text_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "sample.txt")
            self.service.save_text_file(file_path, "Hello, world!")

            self.assertEqual(self.service.read_text_file(file_path), "Hello, world!")
            self.assertEqual(self.service.read_file(file_path), "Hello, world!")

    def test_read_file_falls_back_to_text_reader_for_unknown_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "sample.unknown")
            self.service.save_text_file(file_path, "Fallback content")

            self.assertEqual(self.service.read_file(file_path), "Fallback content")

    def test_is_text_extension(self):
        self.assertTrue(self.service.is_text_extension("document.txt"))
        self.assertTrue(self.service.is_text_extension("document.pdf"))

    def test_supported_text_extensions_contains_text_types(self):
        extensions = self.service.supported_text_extensions()
        self.assertIn(".txt", extensions)
        self.assertIn(".md", extensions)
