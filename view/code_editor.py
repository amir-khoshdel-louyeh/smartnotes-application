"""Code editor with line numbers, grammar-based highlighting and editing aids.

Syntax highlighting is grammar-based through Pygments, which covers Python,
Markdown, JSON, JavaScript/TypeScript, HTML/CSS, SQL, C/C++, Rust, Go, Java and
many other languages. A small regex fallback keeps Python/Markdown/JSON working
if Pygments is unavailable. The editor also paints line numbers, highlights the
current line, matches brackets under the cursor and auto-indents new lines.
"""

import os

from PyQt5.QtCore import QRect, QRegularExpression, QSize, Qt
from PyQt5.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QFontMetricsF,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PyQt5.QtWidgets import QApplication, QPlainTextEdit, QTextEdit, QWidget

from view.styles import palette_for

try:  # Pygments provides the grammars used for real syntax highlighting.
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
    from pygments.token import Token
except ImportError:  # pragma: no cover - optional dependency guard
    get_lexer_by_name = None
    get_lexer_for_filename = None
    Token = None

PYGMENTS_AVAILABLE = get_lexer_by_name is not None

# A full-document token pass keeps multi-line constructs correct. Very large
# files use a faster per-block pass instead to keep typing responsive.
FULL_DOCUMENT_HIGHLIGHT_LIMIT = 200_000

LANGUAGE_BY_EXTENSION = {
    # Documents
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "plain",
    ".rst": "rst",
    # Data / config
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".xml": "xml",
    ".svg": "xml",
    ".diff": "diff",
    ".patch": "diff",
    # Python
    ".py": "python",
    ".pyw": "python",
    # Web
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".vue": "vue",
    # Systems / backend
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".lua": "lua",
    ".dart": "dart",
    ".scala": "scala",
    ".r": "r",
    ".pl": "perl",
    ".ex": "elixir",
    ".exs": "elixir",
    # Shell / database
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".sql": "sql",
    ".dockerfile": "docker",
}

BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
CLOSING_BRACKETS = {closing: opening for opening, closing in BRACKET_PAIRS.items()}
ALL_BRACKETS = set(BRACKET_PAIRS) | set(CLOSING_BRACKETS)


def language_for_path(file_path: str | None) -> str:
    """Return the highlighter language for a file path."""
    if not file_path:
        return "plain"
    return LANGUAGE_BY_EXTENSION.get(os.path.splitext(file_path)[1].lower(), "plain")


def matching_bracket_positions(
    text: str, index: int
) -> tuple[int | None, int | None] | None:
    """Return the positions of a bracket and its match.

    ``(index, None)`` means an opening bracket without a match and
    ``(None, index)`` means a closing bracket without a match. ``None`` means
    the character at ``index`` is not a bracket.
    """
    if not text or index < 0 or index >= len(text):
        return None

    character = text[index]
    if character in BRACKET_PAIRS:
        closing = BRACKET_PAIRS[character]
        depth = 0
        for position in range(index, len(text)):
            current = text[position]
            if current == character:
                depth += 1
            elif current == closing:
                depth -= 1
                if depth == 0:
                    return index, position
        return index, None

    if character in CLOSING_BRACKETS:
        opening = CLOSING_BRACKETS[character]
        depth = 0
        for position in range(index, -1, -1):
            current = text[position]
            if current == character:
                depth += 1
            elif current == opening:
                depth -= 1
                if depth == 0:
                    return position, index
        return None, index

    return None


def indent_for_new_line(prefix: str, width: int = 4) -> str:
    """Return the indentation for a new line after ``prefix``."""
    line = prefix or ""
    stripped = line.lstrip(" \t")
    indentation = line[: len(line) - len(stripped)]
    if not stripped:
        return indentation
    if stripped.endswith((":", "{", "[", "(")):
        return indentation + " " * width
    return indentation


def dedent_line(line: str, width: int = 4) -> str:
    """Remove one indentation level from ``line``."""
    if line.startswith("\t"):
        return line[1:]
    spaces = len(line) - len(line.lstrip(" "))
    return line[min(spaces, width) :]


def _current_theme() -> str:
    app = QApplication.instance()
    theme = app.property("theme") if app is not None else None
    return "dark" if theme == "dark" else "light"


class SyntaxHighlighter(QSyntaxHighlighter):
    """Theme-aware, grammar-based syntax highlighting."""

    TRIPLE_DOUBLE_STATE = 1
    TRIPLE_SINGLE_STATE = 2
    MARKDOWN_CODE_STATE = 3

    def __init__(
        self,
        document,
        theme: str = "light",
        language: str = "plain",
        file_path: str | None = None,
    ):
        super().__init__(document)
        self._theme = theme or "light"
        self._language = language or "plain"
        self._file_path = file_path
        self._lexer = None
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._formats: dict[str, QTextCharFormat] = {}
        self._block_formats: dict[int, list[tuple[int, int, QTextCharFormat]]] = {}
        self._cache_valid = False
        self.document().contentsChange.connect(self._invalidate_cache)
        self._build()

    @property
    def language(self) -> str:
        return self._language

    def apply_theme(self, theme: str) -> None:
        self._theme = theme or "light"
        self._build_formats()
        self._invalidate_cache()
        self.rehighlight()

    def set_language(self, language: str) -> None:
        if language == self._language:
            return
        self._language = language or "plain"
        self._build_lexer()
        self._build_rules()
        self._invalidate_cache()
        self.rehighlight()

    def set_file_path(self, file_path: str | None) -> None:
        self._file_path = file_path
        self._language = language_for_path(file_path)
        self._build_lexer()
        self._build_rules()
        self._invalidate_cache()
        self.rehighlight()

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _format(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        if bold:
            text_format.setFontWeight(QFont.Bold)
        if italic:
            text_format.setFontItalic(True)
        return text_format

    def _build(self) -> None:
        self._build_formats()
        self._build_lexer()
        self._build_rules()
        self._invalidate_cache()

    def _build_formats(self) -> None:
        tokens = palette_for(self._theme)
        self._formats = {
            "keyword": self._format(tokens["syntax_keyword"], bold=True),
            "function": self._format(tokens["syntax_function"]),
            "class": self._format(tokens["syntax_class"], bold=True),
            "string": self._format(tokens["syntax_string"]),
            "comment": self._format(tokens["syntax_comment"], italic=True),
            "number": self._format(tokens["syntax_number"]),
            "markup": self._format(tokens["syntax_markup"], bold=True),
            "emphasis": self._format(tokens["text"], italic=True),
        }

    def _build_lexer(self) -> None:
        self._lexer = None
        if not PYGMENTS_AVAILABLE:
            return
        try:
            if self._language and self._language != "plain":
                self._lexer = get_lexer_by_name(
                    self._language, stripnl=False, ensurenl=False
                )
            elif self._file_path:
                self._lexer = get_lexer_for_filename(
                    self._file_path, stripnl=False, ensurenl=False
                )
        except Exception:  # unknown language or lexer failure
            self._lexer = None

    def _build_rules(self) -> None:
        """Regex fallback used only when no Pygments grammar is available."""
        self._rules = []
        if self._lexer is not None:
            return

        formats = self._formats
        add = lambda pattern, kind: self._rules.append(  # noqa: E731
            (QRegularExpression(pattern), formats[kind])
        )

        if self._language == "python":
            add(
                r"\b(?:False|None|True|and|as|assert|async|await|break|class|continue|"
                r"def|del|elif|else|except|finally|for|from|global|if|import|in|is|"
                r"lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b",
                "keyword",
            )
            add(r"^\s*@[\w.]+", "function")
            add(r"(?<=def )\w+", "function")
            add(r"(?<=class )\w+", "class")
            add(r"\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?)\b", "number")
            add(r"#[^\n]*", "comment")
            add(r'"(?:[^"\\]|\\.)*"', "string")
            add(r"'(?:[^'\\]|\\.)*'", "string")
        elif self._language == "markdown":
            add(r"^#{1,6} .*$", "markup")
            add(r"\*\*[^*\n]+\*\*", "markup")
            add(r"^\s*[-*+]\s", "keyword")
            add(r"^>.*$", "comment")
            add(r"\[[^\]\n]+\]\([^)\n]+\)", "function")
            add(r"`[^`\n]+`", "string")
        elif self._language == "json":
            add(r"\b(?:true|false|null)\b", "keyword")
            add(r"-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b", "number")
            add(r'"[^"\n]*"', "string")
            add(r'"[^"\n]*"(?=\s*:)', "markup")

    def _invalidate_cache(self, *_args) -> None:
        self._cache_valid = False
        self._block_formats = {}

    # ------------------------------------------------------------------ token mapping
    def _format_for_token(self, token_type) -> QTextCharFormat | None:
        if Token is None:
            return None
        if token_type in Token.Comment:
            return self._formats["comment"]
        if token_type in Token.Keyword:
            return self._formats["keyword"]
        if token_type in Token.Name.Function or token_type in Token.Name.Decorator:
            return self._formats["function"]
        if token_type in Token.Name.Class or token_type in Token.Name.Builtin:
            return self._formats["class"]
        if token_type in Token.Name.Tag:
            return self._formats["markup"]
        if token_type in Token.Name.Attribute:
            return self._formats["function"]
        if token_type in Token.Literal.Number:
            return self._formats["number"]
        if token_type in Token.Literal.String:
            return self._formats["string"]
        if (
            token_type in Token.Generic.Heading
            or token_type in Token.Generic.Subheading
            or token_type in Token.Generic.Strong
        ):
            return self._formats["markup"]
        if token_type in Token.Generic.Emph:
            return self._formats["emphasis"]
        return None

    # ------------------------------------------------------------------ painting
    def highlightBlock(self, text: str) -> None:
        if self._lexer is not None:
            self._highlight_with_grammar(text)
            return
        self._highlight_with_rules(text)

    def _highlight_with_grammar(self, text: str) -> None:
        self.setCurrentBlockState(0)
        if self.document().characterCount() > FULL_DOCUMENT_HIGHLIGHT_LIMIT:
            # Large file: tokenise this block only to keep typing responsive.
            offset = 0
            for token_type, value in self._lexer.get_tokens(text):
                text_format = self._format_for_token(token_type)
                if text_format is not None and value:
                    self.setFormat(offset, len(value), text_format)
                offset += len(value)
            return

        if not self._cache_valid:
            self._rebuild_cache()

        for start, length, text_format in self._block_formats.get(
            self.currentBlock().blockNumber(), ()
        ):
            start = max(0, start)
            length = min(length, len(text) - start)
            if length > 0:
                self.setFormat(start, length, text_format)

    def _rebuild_cache(self) -> None:
        self._block_formats = {}
        self._cache_valid = True
        if self._lexer is None:
            return

        text = self.document().toPlainText()
        if not text:
            return

        block_number = 0
        column = 0
        try:
            for token_type, value in self._lexer.get_tokens(text):
                text_format = self._format_for_token(token_type)
                parts = value.split("\n")
                for index, part in enumerate(parts):
                    if part and text_format is not None:
                        self._block_formats.setdefault(block_number, []).append(
                            (column, len(part), text_format)
                        )
                    column += len(part)
                    if index < len(parts) - 1:
                        block_number += 1
                        column = 0
        except Exception:  # pragma: no cover - malformed lexer input
            self._block_formats = {}

    def _highlight_with_rules(self, text: str) -> None:
        for pattern, text_format in self._rules:
            matches = pattern.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)

        if self._language == "python":
            self._highlight_python_strings(text)
        elif self._language == "markdown":
            self._highlight_markdown_code(text)
        else:
            self.setCurrentBlockState(0)

    def _highlight_python_strings(self, text: str) -> None:
        string_format = self._formats["string"]
        state = self.previousBlockState()

        if state in (self.TRIPLE_DOUBLE_STATE, self.TRIPLE_SINGLE_STATE):
            delimiter = '"""' if state == self.TRIPLE_DOUBLE_STATE else "'''"
            end = text.find(delimiter)
            if end == -1:
                self.setFormat(0, len(text), string_format)
                self.setCurrentBlockState(state)
                return
            self.setFormat(0, end + 3, string_format)
            self.setCurrentBlockState(0)
            return

        candidates = []
        for delimiter, state_id in (
            ('"""', self.TRIPLE_DOUBLE_STATE),
            ("'''", self.TRIPLE_SINGLE_STATE),
        ):
            index = text.find(delimiter)
            if index >= 0:
                candidates.append((index, delimiter, state_id))

        if not candidates:
            self.setCurrentBlockState(0)
            return

        start, delimiter, state_id = min(candidates)
        end = text.find(delimiter, start + 3)
        if end == -1:
            self.setFormat(start, len(text) - start, string_format)
            self.setCurrentBlockState(state_id)
        else:
            self.setFormat(start, end + 3 - start, string_format)
            self.setCurrentBlockState(0)

    def _highlight_markdown_code(self, text: str) -> None:
        code_format = self._formats["string"]
        if self.previousBlockState() == self.MARKDOWN_CODE_STATE:
            end = text.find("```")
            if end == -1:
                self.setFormat(0, len(text), code_format)
                self.setCurrentBlockState(self.MARKDOWN_CODE_STATE)
                return
            self.setFormat(0, end + 3, code_format)
            self.setCurrentBlockState(0)
            return

        start = text.find("```")
        if start < 0:
            self.setCurrentBlockState(0)
            return

        end = text.find("```", start + 3)
        if end == -1:
            self.setFormat(start, len(text) - start, code_format)
            self.setCurrentBlockState(self.MARKDOWN_CODE_STATE)
        else:
            self.setFormat(start, end + 3 - start, code_format)
            self.setCurrentBlockState(0)


class LineNumberArea(QWidget):
    """Gutter painted by the editor."""

    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Plain-text editor with line numbers, highlighting and editing aids."""

    INDENT_WIDTH = 4

    def __init__(self, file_path: str | None = None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._theme = _current_theme()
        self.document().setDocumentMargin(10)

        self.line_number_area = LineNumberArea(self)
        self.highlighter = SyntaxHighlighter(
            self.document(),
            self._theme,
            language_for_path(file_path),
            file_path=file_path,
        )

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._update_current_line)
        self.textChanged.connect(self._update_current_line)
        self.setCursorWidth(2)
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        if not file_path:
            self.setPlaceholderText("Create or open a file to start studying...")

        self._update_line_number_area_width()
        self._update_current_line()

    @property
    def language(self) -> str:
        return self.highlighter.language

    def set_file_path(self, file_path: str | None) -> None:
        self.file_path = file_path
        self.highlighter.set_file_path(file_path)
        self.setPlaceholderText(
            "" if file_path else "Create or open a file to start studying..."
        )

    def apply_theme(self, theme: str) -> None:
        self._theme = theme or "light"
        self.highlighter.apply_theme(self._theme)
        self._update_line_number_area_width()
        self.line_number_area.update()
        self._update_current_line()

    # ------------------------------------------------------------------ gutter
    def line_number_area_width(self) -> int:
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 18 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _block_count: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        contents = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(
                contents.left(),
                contents.top(),
                self.line_number_area_width(),
                contents.height(),
            )
        )

    def line_number_area_paint_event(self, event) -> None:
        tokens = palette_for(self._theme)
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(tokens["surface_alt"]))
        painter.setPen(QColor(tokens["border"]))
        painter.drawLine(
            self.line_number_area.width() - 1,
            event.rect().top(),
            self.line_number_area.width() - 1,
            event.rect().bottom(),
        )

        gutter_font = QFont(self.font())
        if gutter_font.pointSize() > 8:
            gutter_font.setPointSize(gutter_font.pointSize() - 1)
        painter.setFont(gutter_font)
        metrics = QFontMetrics(gutter_font)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())
        current_block = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                is_current = block_number == current_block
                painter.setPen(
                    QColor(tokens["accent"] if is_current else tokens["muted"])
                )
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    metrics.height(),
                    Qt.AlignRight | Qt.AlignVCenter,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ------------------------------------------------------------------ decorations
    def _update_current_line(self) -> None:
        tokens = palette_for(self._theme)
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(tokens["surface_alt"]))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        selections = [selection]
        selections.extend(self._bracket_extra_selections())
        self.setExtraSelections(selections)

    def _bracket_extra_selections(self) -> list:
        text = self.toPlainText()
        position = self.textCursor().position()
        index = None
        if position < len(text) and text[position] in ALL_BRACKETS:
            index = position
        elif position > 0 and text[position - 1] in ALL_BRACKETS:
            index = position - 1
        if index is None:
            return []

        matched = matching_bracket_positions(text, index)
        if matched is None:
            return []
        left, right = matched

        tokens = palette_for(self._theme)
        if left is None or right is None:
            unmatched = left if left is not None else right
            text_format = QTextCharFormat()
            text_format.setBackground(QColor(tokens["danger"]))
            text_format.setForeground(QColor(tokens["on_accent"]))
            text_format.setFontWeight(QFont.Bold)
            return [self._character_selection(unmatched, text_format)]

        text_format = QTextCharFormat()
        text_format.setBackground(QColor(tokens["accent"]))
        text_format.setForeground(QColor(tokens["on_accent"]))
        text_format.setFontWeight(QFont.Bold)
        return [
            self._character_selection(left, text_format),
            self._character_selection(right, text_format),
        ]

    def _character_selection(self, index: int, text_format: QTextCharFormat):
        cursor = QTextCursor(self.document())
        cursor.setPosition(index)
        cursor.setPosition(index + 1, QTextCursor.KeepAnchor)
        selection = QTextEdit.ExtraSelection()
        selection.cursor = cursor
        selection.format = text_format
        return selection

    # ------------------------------------------------------------------ editing
    def keyPressEvent(self, event) -> None:
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key_Return, Qt.Key_Enter) and not (
            modifiers & (Qt.ControlModifier | Qt.AltModifier)
        ):
            self._insert_newline_with_indent()
            return

        if key == Qt.Key_Tab and not (modifiers & Qt.ControlModifier):
            if modifiers & Qt.ShiftModifier:
                self._dedent_selection_or_line()
            elif self.textCursor().hasSelection():
                self._shift_selected_lines(1)
            else:
                self._insert_tab_spaces()
            return

        if key == Qt.Key_Backtab:
            self._dedent_selection_or_line()
            return

        if key == Qt.Key_Backspace and self._unindent_on_backspace():
            return

        super().keyPressEvent(event)

    def _insert_newline_with_indent(self) -> None:
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        prefix = cursor.block().text()[: cursor.positionInBlock()]
        indent = indent_for_new_line(prefix, self.INDENT_WIDTH)
        cursor.insertText("\n" + indent)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _insert_tab_spaces(self) -> None:
        cursor = self.textCursor()
        spaces = self.INDENT_WIDTH - (cursor.positionInBlock() % self.INDENT_WIDTH)
        cursor.insertText(" " * spaces)
        self.setTextCursor(cursor)

    def _dedent_selection_or_line(self) -> None:
        if self.textCursor().hasSelection():
            self._shift_selected_lines(-1)
        else:
            self._dedent_current_line()

    def _dedent_current_line(self) -> None:
        cursor = self.textCursor()
        block = cursor.block()
        line = block.text()
        if line.startswith("\t"):
            remove = 1
        else:
            remove = min(self.INDENT_WIDTH, len(line) - len(line.lstrip(" ")))
        if remove <= 0:
            return

        position = cursor.position()
        edit = QTextCursor(block)
        edit.movePosition(QTextCursor.StartOfBlock)
        edit.setPosition(edit.position() + remove, QTextCursor.KeepAnchor)
        edit.removeSelectedText()

        block = self.document().findBlockByNumber(block.blockNumber())
        cursor.setPosition(max(block.position(), position - remove))
        self.setTextCursor(cursor)

    def _shift_selected_lines(self, direction: int) -> None:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        document = self.document()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        first = document.findBlock(start).blockNumber()
        last_block = document.findBlock(end)
        last = last_block.blockNumber()
        if last > first and end == last_block.position():
            last -= 1

        edit = QTextCursor(document)
        edit.beginEditBlock()
        for number in range(first, last + 1):
            block = document.findBlockByNumber(number)
            block_cursor = QTextCursor(block)
            block_cursor.movePosition(QTextCursor.StartOfBlock)
            if direction > 0:
                block_cursor.insertText(" " * self.INDENT_WIDTH)
            else:
                line = block.text()
                if line.startswith("\t"):
                    remove = 1
                else:
                    remove = min(
                        self.INDENT_WIDTH, len(line) - len(line.lstrip(" "))
                    )
                if remove > 0:
                    block_cursor.setPosition(
                        block_cursor.position() + remove, QTextCursor.KeepAnchor
                    )
                    block_cursor.removeSelectedText()
        edit.endEditBlock()

        first_block = document.findBlockByNumber(first)
        last_block = document.findBlockByNumber(last)
        restored = QTextCursor(document)
        restored.setPosition(first_block.position())
        restored.setPosition(
            last_block.position() + len(last_block.text()), QTextCursor.KeepAnchor
        )
        self.setTextCursor(restored)

    def _unindent_on_backspace(self) -> bool:
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        prefix = cursor.block().text()[: cursor.positionInBlock()]
        if not prefix or prefix.strip():
            return False

        remove = 1 if prefix.endswith("\t") else min(self.INDENT_WIDTH, len(prefix))
        position = cursor.position()
        cursor.setPosition(position - remove)
        cursor.setPosition(position, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        return True

    def setFont(self, font: QFont) -> None:
        super().setFont(font)
        if hasattr(self, "line_number_area"):
            self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)
            self._update_line_number_area_width()
            self.line_number_area.update()
