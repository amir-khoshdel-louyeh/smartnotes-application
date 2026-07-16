import unittest

try:
    from view.code_editor import (
        dedent_line,
        indent_for_new_line,
        language_for_path,
        matching_bracket_positions,
    )

    HELPERS_AVAILABLE = True
except Exception:  # PyQt5 is optional in lightweight test environments
    HELPERS_AVAILABLE = False


@unittest.skipUnless(HELPERS_AVAILABLE, "PyQt5 is not available; editor helpers are skipped.")
class TestCodeEditorHelpers(unittest.TestCase):
    def test_language_detection_by_extension(self):
        self.assertEqual(language_for_path("/tmp/note.md"), "markdown")
        self.assertEqual(language_for_path("/tmp/main.py"), "python")
        self.assertEqual(language_for_path("/tmp/app.js"), "javascript")
        self.assertEqual(language_for_path("/tmp/app.tsx"), "tsx")
        self.assertEqual(language_for_path("/tmp/main.rs"), "rust")
        self.assertEqual(language_for_path("/tmp/notes.txt"), "plain")
        self.assertEqual(language_for_path(None), "plain")

    def test_matching_brackets_forward_and_backward(self):
        text = "call(alpha[0])"
        self.assertEqual(matching_bracket_positions(text, 4), (4, 13))
        self.assertEqual(matching_bracket_positions(text, 13), (4, 13))
        self.assertEqual(matching_bracket_positions(text, 12), (10, 12))
        self.assertIsNone(matching_bracket_positions(text, 1))

    def test_unmatched_brackets_are_reported(self):
        self.assertEqual(matching_bracket_positions("(alpha", 0), (0, None))
        self.assertEqual(matching_bracket_positions("alpha)", 5), (None, 5))

    def test_auto_indent_after_block_opener(self):
        self.assertEqual(indent_for_new_line("    if ready:"), "        ")
        self.assertEqual(indent_for_new_line("function run() {"), "    ")
        self.assertEqual(indent_for_new_line("plain text"), "")
        self.assertEqual(indent_for_new_line("    "), "    ")

    def test_dedent_line_removes_one_level(self):
        self.assertEqual(dedent_line("        value = 1"), "    value = 1")
        self.assertEqual(dedent_line("    value = 1"), "value = 1")
        self.assertEqual(dedent_line("value = 1"), "value = 1")
