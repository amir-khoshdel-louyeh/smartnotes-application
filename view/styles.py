"""Centralized design tokens and Qt stylesheets for StudyMate.

The application ships two complete themes (light and dark). Both are rendered
from the same QSS template so every widget stays visually consistent, and the
token dictionaries are reused by the markdown preview and mind-map renderer.
"""

LIGHT: dict[str, str] = {
    "bg": "#f4f6f9",
    "surface": "#ffffff",
    "surface_alt": "#f1f3f7",
    "surface_sunken": "#e6eaf0",
    "border": "#e2e7ee",
    "border_strong": "#cbd3de",
    "text": "#1b2430",
    "muted": "#68758a",
    "accent": "#5b5bd6",
    "accent_hover": "#4a4ac4",
    "accent_soft": "#eceeff",
    "accent_border": "#d3d7ff",
    "on_accent": "#ffffff",
    "success": "#15803d",
    "success_soft": "#e7f6ed",
    "warning": "#b45309",
    "warning_soft": "#fdf2e3",
    "danger": "#d92d20",
    "danger_soft": "#fdecea",
    "syntax_keyword": "#7c3aed",
    "syntax_function": "#1d4ed8",
    "syntax_class": "#0e7490",
    "syntax_string": "#15803d",
    "syntax_comment": "#8b95a5",
    "syntax_number": "#b45309",
    "syntax_markup": "#be185d",
    "tooltip_bg": "#1b2430",
    "tooltip_fg": "#f7f9fc",
}

DARK: dict[str, str] = {
    "bg": "#121418",
    "surface": "#191c22",
    "surface_alt": "#20242c",
    "surface_sunken": "#161920",
    "border": "#2a2f38",
    "border_strong": "#3b424e",
    "text": "#e7ebf1",
    "muted": "#98a3b3",
    "accent": "#8b93ff",
    "accent_hover": "#a4abff",
    "accent_soft": "#232a44",
    "accent_border": "#3b4590",
    "on_accent": "#101218",
    "success": "#4ade80",
    "success_soft": "#1c3327",
    "warning": "#fbbf24",
    "warning_soft": "#3a2f1a",
    "danger": "#f87171",
    "danger_soft": "#3a2225",
    "syntax_keyword": "#c4b5fd",
    "syntax_function": "#93c5fd",
    "syntax_class": "#7dd3fc",
    "syntax_string": "#86efac",
    "syntax_comment": "#8b95a5",
    "syntax_number": "#fcd34d",
    "syntax_markup": "#f0abfc",
    "tooltip_bg": "#e7ebf1",
    "tooltip_fg": "#121418",
}

_TEMPLATE = """
/* ---------- Base ---------- */
QWidget {
    color: $text;
    font-family: "Inter", "Segoe UI", "Cantarell", "Ubuntu", sans-serif;
}
QMainWindow, QDialog {
    background-color: $bg;
}
QMainWindow::separator {
    background-color: $bg;
    width: 6px;
    height: 6px;
}
QMainWindow::separator:hover {
    background-color: $accent_soft;
}

/* ---------- Cards & typography ---------- */
QFrame#Card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 10px;
}
QFrame#SidebarHeader {
    background-color: $surface;
    border-bottom: 1px solid $border;
}
QFrame#SidebarFooter {
    background-color: $surface;
    border-top: 1px solid $border;
}
QFrame#FindBar {
    background-color: $surface_alt;
    border-bottom: 1px solid $border;
}
QLabel#AppTitle {
    font-size: 15pt;
    font-weight: 700;
    color: $text;
}
QLabel#AppSubtitle {
    color: $muted;
    font-size: 8.5pt;
}
QLabel#CardTitle {
    font-size: 10pt;
    font-weight: 600;
    color: $text;
}
QLabel#SectionLabel {
    color: $muted;
    font-size: 8.5pt;
    font-weight: 600;
}
QLabel#Hint {
    color: $muted;
    font-size: 9pt;
}
QLabel#EmptyState {
    color: $muted;
    font-size: 9.5pt;
}
QLabel#Pill {
    background-color: $accent_soft;
    color: $accent;
    border: 1px solid $accent_border;
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 8.5pt;
    font-weight: 600;
}
QLabel#DangerPill {
    background-color: $danger_soft;
    color: $danger;
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 8.5pt;
    font-weight: 600;
}

/* ---------- Menus ---------- */
QMenuBar {
    background-color: $surface;
    border-bottom: 1px solid $border;
    padding: 2px 6px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background-color: $surface_alt;
}
QMenu {
    background-color: $surface;
    border: 1px solid $border;
    padding: 6px;
}
QMenu::item {
    padding: 7px 28px 7px 12px;
    border-radius: 5px;
    color: $text;
}
QMenu::item:selected {
    background-color: $accent_soft;
    color: $accent;
}
QMenu::item:disabled {
    color: $muted;
}
QMenu::separator {
    height: 1px;
    background-color: $border;
    margin: 5px 10px;
}

/* ---------- Toolbars ---------- */
QToolBar {
    background-color: $surface;
    border: none;
    border-bottom: 1px solid $border;
    padding: 5px 8px;
    spacing: 3px;
}
QToolBar::separator {
    background-color: $border;
    width: 1px;
    height: 18px;
    margin: 0 7px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 5px 10px;
    color: $text;
}
QToolButton:hover {
    background-color: $surface_alt;
    border-color: $border;
}
QToolButton:pressed {
    background-color: $surface_sunken;
}
QToolButton:checked {
    background-color: $accent_soft;
    color: $accent;
    border-color: $accent_border;
}
QToolButton:disabled {
    color: $muted;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 7px;
    padding: 7px 14px;
    min-height: 16px;
}
QPushButton:hover {
    background-color: $surface_alt;
}
QPushButton:pressed {
    background-color: $surface_sunken;
}
QPushButton:disabled {
    color: $muted;
    border-color: $border;
    background-color: $surface_alt;
}
QPushButton:default {
    border-color: $accent;
}
QPushButton#Primary {
    background-color: $accent;
    color: $on_accent;
    border: 1px solid $accent;
    font-weight: 600;
}
QPushButton#Primary:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
QPushButton#Primary:disabled {
    background-color: $surface_sunken;
    color: $muted;
    border-color: $border;
}
QPushButton#Danger {
    color: $danger;
    border-color: $border;
    background-color: transparent;
}
QPushButton#Danger:hover {
    background-color: $danger_soft;
    border-color: $danger;
}
QPushButton#Ghost {
    background-color: transparent;
    border-color: transparent;
    color: $muted;
    padding: 6px 10px;
}
QPushButton#Ghost:hover {
    background-color: $surface_alt;
    color: $text;
    border-color: $border;
}
QPushButton#IconButton {
    background-color: transparent;
    border: none;
    border-radius: 7px;
    padding: 2px 4px;
    color: $muted;
    min-width: 22px;
    max-width: 26px;
    min-height: 22px;
}
QPushButton#IconButton:hover {
    background-color: $surface_alt;
    color: $text;
}
QPushButton#LinkButton {
    background: transparent;
    border: none;
    color: $accent;
    padding: 2px;
    text-align: left;
}
QPushButton#LinkButton:hover {
    color: $accent_hover;
}

/* ---------- Inputs ---------- */
QLineEdit, QSpinBox, QComboBox, QFontComboBox {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 7px;
    padding: 6px 9px;
    min-height: 16px;
    selection-background-color: $accent;
    selection-color: $on_accent;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QFontComboBox:focus {
    border-color: $accent;
}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    color: $muted;
    background-color: $surface_alt;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: $surface;
    border: 1px solid $border;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 6px 8px;
    border-radius: 5px;
}
QComboBox QAbstractItemView::item:selected {
    background-color: $accent_soft;
    color: $accent;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    border: none;
    background: transparent;
}

QCheckBox {
    spacing: 8px;
    color: $text;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 1px solid $border_strong;
    background-color: $surface;
}
QCheckBox::indicator:hover {
    border-color: $accent;
}
QCheckBox::indicator:checked {
    background-color: $accent;
    border-color: $accent;
}

/* ---------- Text areas ---------- */
QTextEdit, QPlainTextEdit {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 14px 16px;
    selection-background-color: $accent;
    selection-color: $on_accent;
}
QPlainTextEdit {
    /* The code editor paints its own gutter and document margins. */
    padding: 0;
}
QTextBrowser#PreviewBrowser {
    background-color: $surface;
    border: none;
    border-radius: 0;
    padding: 22px 26px;
}
QTextEdit#AIOutput {
    background-color: $surface_alt;
    border: 1px solid $border;
    font-size: 9.5pt;
}

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid $border;
    background-color: $surface;
    border-radius: 9px;
    top: -1px;
}
QTabBar::tab {
    background-color: transparent;
    color: $muted;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 7px 14px;
    margin-right: 4px;
}
QTabBar::tab:hover:!selected {
    background-color: $surface_alt;
    color: $text;
}
QTabBar::tab:selected {
    background-color: $surface;
    color: $text;
    border-color: $border;
    font-weight: 600;
}
QTabBar::close-button {
    subcontrol-position: right;
}
QTabWidget#SidebarTabs::pane {
    border: none;
    background-color: $bg;
    border-radius: 0;
}
QTabWidget#SidebarTabs QTabBar {
    background-color: transparent;
    padding: 0 4px;
}
QTabWidget#SidebarTabs QTabBar::tab {
    background-color: transparent;
    border: none;
    color: $muted;
    padding: 9px 10px;
    margin: 6px 2px 2px 2px;
    border-radius: 7px;
    font-weight: 500;
}
QTabWidget#SidebarTabs QTabBar::tab:hover {
    background-color: $surface_alt;
    color: $text;
}
QTabWidget#SidebarTabs QTabBar::tab:selected {
    background-color: $accent_soft;
    color: $accent;
    font-weight: 600;
}

/* ---------- Item views ---------- */
QTreeView, QListView, QListWidget {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QTreeView::item, QListView::item, QListWidget::item {
    padding: 5px;
    border-radius: 6px;
}
QTreeView::item:hover, QListView::item:hover, QListWidget::item:hover {
    background-color: $surface_alt;
}
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected {
    background-color: $accent_soft;
    color: $accent;
}
QTreeView::branch {
    background: transparent;
}
QHeaderView::section {
    background-color: $surface_alt;
    color: $muted;
    border: none;
    padding: 5px 6px;
}
QListWidget {
    background-color: $surface;
    border: none;
    padding: 0;
}
QListWidget::item {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 0;
    margin-bottom: 6px;
}
QListWidget::item:selected {
    background-color: $accent_soft;
    border-color: $accent_border;
    color: $text;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: $border_strong;
    min-height: 28px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: $muted;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: $border_strong;
    min-width: 28px;
    border-radius: 3px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0;
    height: 0;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}
QScrollArea {
    border: none;
    background: transparent;
}

/* ---------- Progress ---------- */
QProgressBar {
    background-color: $surface_sunken;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: $accent;
    border-radius: 4px;
}

/* ---------- Docks, status bar, tooltips ---------- */
QDockWidget {
    color: $text;
    border: none;
}
QDockWidget::title {
    background-color: $surface;
    border-bottom: 1px solid $border;
    padding: 7px 10px;
    text-align: left;
}
QStatusBar {
    background-color: $surface;
    border-top: 1px solid $border;
    color: $muted;
}
QStatusBar::item {
    border: none;
}
QStatusBar QLabel {
    color: $muted;
    padding: 0 8px;
}
QToolTip {
    background-color: $tooltip_bg;
    color: $tooltip_fg;
    border: 1px solid $border_strong;
    padding: 5px 8px;
    border-radius: 6px;
}
QSplitter::handle {
    background-color: transparent;
}
QSplitter::handle:horizontal {
    width: 6px;
}
QSplitter::handle:hover {
    background-color: $accent_soft;
}
"""


def _render(tokens: dict[str, str]) -> str:
    """Substitute ``$token`` placeholders, longest names first to avoid prefixes."""
    css = _TEMPLATE
    for key in sorted(tokens, key=len, reverse=True):
        css = css.replace(f"${key}", tokens[key])
    return css


LIGHT_STYLESHEET = _render(LIGHT)
DARK_STYLESHEET = _render(DARK)


def palette_for(theme: str) -> dict[str, str]:
    """Return the token dictionary for ``theme`` ("light" or "dark")."""
    return dict(DARK if (theme or "").lower() == "dark" else LIGHT)


def stylesheet_for(theme: str) -> str:
    """Return the complete stylesheet for ``theme``."""
    return DARK_STYLESHEET if (theme or "").lower() == "dark" else LIGHT_STYLESHEET
