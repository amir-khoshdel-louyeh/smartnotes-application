"""Centralized Qt stylesheets for StudyMate themes."""

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", "Cantarell", "sans-serif";
    font-size: 10pt;
}
QTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    font-family: "Consolas", "Monaco", "monospace";
    font-size: 11pt;
}
QDockWidget {
    background-color: #252526;
    color: #cccccc;
}
QDockWidget::title {
    text-align: left;
    background: #3c3c3c;
    padding-left: 5px;
}
QMenuBar {
    background-color: #3c3c3c;
    color: #cccccc;
}
QMenuBar::item:selected {
    background-color: #505050;
}
QMenu {
    background-color: #252526;
    border: 1px solid #3c3c3c;
}
QMenu::item:selected {
    background-color: #094771;
    color: #ffffff;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
}
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555;
    padding: 4px 8px;
    border-radius: 2px;
}
QPushButton:hover {
    background-color: #4c4c4c;
}
QPushButton:pressed {
    background-color: #5c5c5c;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #aaaaaa;
    padding: 8px;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid #3c3c3c;
}
QScrollBar:vertical {
    border: none;
    background: #252526;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #4a4a4a;
    min-height: 20px;
}
QScrollBar:horizontal {
    border: none;
    background: #252526;
    height: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #4a4a4a;
    min-width: 20px;
}
"""
