"""Theme handling extracted from the MainWindow God class."""

from PyQt5.QtWidgets import QApplication

from view.styles import stylesheet_for


class ThemeManager:
    """Applies light/dark themes and syncs sidebar/menu state."""

    @staticmethod
    def apply(theme_name: str):
        app = QApplication.instance()
        if app is None:
            return
        theme = (theme_name or "light").lower()
        app.setProperty("theme", "dark" if theme == "dark" else "light")
        app.setStyleSheet(stylesheet_for(theme))

    @staticmethod
    def apply_dark():
        ThemeManager.apply("dark")

    @staticmethod
    def apply_light(sidebar=None):
        # The sidebar argument is kept for backwards compatibility.
        ThemeManager.apply("light")

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
