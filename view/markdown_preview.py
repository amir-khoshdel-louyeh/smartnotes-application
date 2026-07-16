"""Live markdown preview dock rendered with QTextDocument."""

import html
import os
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget, QTextBrowser

from view.styles import palette_for


def _document_css(tokens: dict[str, str]) -> str:
    return f"""
    body {{
        color: {tokens['text']};
        background-color: {tokens['surface']};
        font-family: 'Inter', 'Segoe UI', 'Cantarell', sans-serif;
        font-size: 11pt;
        line-height: 1.55;
    }}
    h1, h2, h3, h4 {{
        color: {tokens['text']};
        font-weight: 700;
        margin-top: 18px;
        margin-bottom: 8px;
    }}
    h1 {{ font-size: 20pt; }}
    h2 {{ font-size: 16pt; }}
    h3 {{ font-size: 13pt; }}
    p {{ margin: 8px 0; }}
    a {{ color: {tokens['accent']}; text-decoration: none; }}
    code {{
        background-color: {tokens['surface_alt']};
        color: {tokens['accent']};
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 9.5pt;
    }}
    pre {{
        background-color: {tokens['surface_alt']};
        color: {tokens['text']};
        padding: 10px;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        font-size: 9.5pt;
        margin: 10px 0;
    }}
    blockquote {{
        color: {tokens['muted']};
        border-left: 3px solid {tokens['accent_border']};
        margin: 10px 0;
        padding-left: 12px;
    }}
    hr {{
        color: {tokens['border']};
    }}
    table {{
        border-collapse: collapse;
    }}
    th, td {{
        border: 1px solid {tokens['border']};
        padding: 5px 8px;
    }}
    th {{
        background-color: {tokens['surface_alt']};
    }}
    .muted {{
        color: {tokens['muted']};
    }}
    """


FENCED_CODE = re.compile(r"```[^\n`]*\n(.*?)```", re.DOTALL)
CODE_MARKER = "STUDYMATE_CODE_BLOCK_{}_END"


def _code_block_html(code: str, tokens: dict[str, str]) -> str:
    """Render code with explicit line breaks (Qt rich text ignores <pre>)."""
    escaped = html.escape(code).replace("\n", "<br/>")
    return (
        f'<p style="background-color:{tokens["surface_alt"]}; color:{tokens["text"]}; '
        "font-family:'JetBrains Mono','Consolas',monospace; font-size:9.5pt; "
        f'margin:10px 0;">{escaped}</p>'
    )


def _extract_code_blocks(text: str) -> tuple[str, list[str]]:
    """Pull fenced code out of markdown (Qt's parser does not support fences)."""
    blocks: list[str] = []

    def _replace(match: re.Match) -> str:
        blocks.append(match.group(1).rstrip("\n"))
        return f"\n\n{CODE_MARKER.format(len(blocks) - 1)}\n\n"

    return FENCED_CODE.sub(_replace, text), blocks


class MarkdownPreviewDock(QDockWidget):
    """Right-hand dock that renders the current editor content."""

    def __init__(self, parent=None):
        super().__init__("Preview", parent)
        self.setObjectName("PreviewDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.setMinimumWidth(300)

        self.browser = QTextBrowser()
        self.browser.setObjectName("PreviewBrowser")
        self.browser.setOpenExternalLinks(True)
        self.browser.setFrameShape(QTextBrowser.NoFrame)
        self.setWidget(self.browser)

        self._source = ""
        self._theme = "light"
        self._filename = ""

    def set_source(self, text: str, theme: str = "light", filename: str = "") -> None:
        self._source = text or ""
        self._theme = theme or "light"
        self._filename = filename or ""
        if self._filename:
            self.setWindowTitle(f"Preview · {os.path.basename(self._filename)}")
        else:
            self.setWindowTitle("Preview · Untitled")
        self._render()

    def set_theme(self, theme: str) -> None:
        self._theme = theme or "light"
        self._render()

    def _is_markdown(self) -> bool:
        if not self._filename:
            return True
        return self._filename.lower().endswith((".md", ".markdown"))

    def _render(self) -> None:
        tokens = palette_for(self._theme)
        document = self.browser.document()
        document.setDefaultStyleSheet(_document_css(tokens))

        if not self._source.strip():
            document.setHtml(
                "<p class='muted' style='margin-top:28px;'>"
                "Nothing to preview yet. Open a note or start typing."
                "</p>"
            )
            return

        if self._is_markdown() and hasattr(document, "setMarkdown"):
            markdown, code_blocks = _extract_code_blocks(self._source)
            document.setMarkdown(markdown)
            if code_blocks:
                rendered = document.toHtml()
                for index, code in enumerate(code_blocks):
                    pattern = re.compile(
                        rf"<p[^>]*>\s*{CODE_MARKER.format(index)}\s*</p>", re.IGNORECASE
                    )
                    rendered = pattern.sub(
                        lambda _match, body=code: _code_block_html(body, tokens), rendered
                    )
                document.setHtml(rendered)
        else:
            document.setHtml(f"<pre>{html.escape(self._source)}</pre>")
