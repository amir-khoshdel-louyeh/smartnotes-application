"""Theme handling extracted from MainWindow God class."""

from PyQt5.QtWidgets import QApplication
from view.styles import DARK_STYLESHEET


class ThemeManager:
    """Applies light/dark themes and syncs sidebar/menu state."""

    @staticmethod
    def apply_dark():
        QApplication.instance().setProperty("theme", "dark")
        QApplication.instance().setStyleSheet(DARK_STYLESHEET)

    @staticmethod
    def apply_light(sidebar):
        QApplication.instance().setStyleSheet("")
        QApplication.instance().setProperty("theme", "light")
        sidebar.setStyleSheet("")

    @staticmethod
    def sync_ui(sidebar, menu_actions, theme_name: str):
        theme = theme_name.lower()
        is_dark = theme == "dark"
        sidebar.theme_combo.blockSignals(True)
        menu_actions["dark_mode"].blockSignals(True)
        sidebar.theme_combo.setCurrentText(theme.capitalize())
        menu_actions["dark_mode"].setChecked(is_dark)
        sidebar.theme_combo.blockSignals(False)
        menu_actions["dark_mode"].blockSignals(False)
