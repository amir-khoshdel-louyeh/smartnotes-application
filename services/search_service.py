import re


class SearchService:
    """Logic for text search and replace operations in editor widgets."""

    @staticmethod
    def find_next(editor, query, case_sensitive=False):
        if not query or not query.strip():
            return False

        from PyQt5.QtGui import QTextDocument, QTextCursor

        flags = QTextDocument.FindFlags()
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensibly

        found = editor.find(query, flags)
        if not found:
            editor.moveCursor(QTextCursor.Start)
            found = editor.find(query, flags)
        return found

    @staticmethod
    def find_previous(editor, query, case_sensitive=False):
        if not query or not query.strip():
            return False

        from PyQt5.QtGui import QTextDocument, QTextCursor

        flags = QTextDocument.FindFlags() | QTextDocument.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensibly

        found = editor.find(query, flags)
        if not found:
            editor.moveCursor(QTextCursor.End)
            found = editor.find(query, flags)
        return found

    @staticmethod
    def replace_current(editor, query, replace_text, case_sensitive=False):
        if not query or not query.strip():
            return False

        cursor = editor.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            matches = selected_text == query if case_sensitive else selected_text.lower() == query.lower()
            if matches:
                cursor.insertText(replace_text)
                return True

        return SearchService.find_next(editor, query, case_sensitive) and SearchService.replace_current(editor, query, replace_text, case_sensitive)

    @staticmethod
    def replace_all(text, query, replace_text, case_sensitive=False):
        if not query:
            return text, 0

        flags = 0 if case_sensitive else re.IGNORECASE
        new_text, count = re.subn(re.escape(query), replace_text, text, flags=flags)
        return new_text, count
