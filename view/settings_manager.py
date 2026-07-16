from PyQt5.QtCore import QSettings


class SettingsManager:
    """A simple wrapper around QSettings for application preferences."""

    def __init__(self):
        self._settings = QSettings("StudyMate", "StudyMate")

    def value(self, key, default=None, type=None):
        if type is not None:
            return self._settings.value(key, default, type=type)
        return self._settings.value(key, default)

    def setValue(self, key, value):
        self._settings.setValue(key, value)

    def sync(self):
        self._settings.sync()

    def load_settings(self):
        """Load the current saved settings into a SettingsModel."""
        from view.settings_model import SettingsModel

        return SettingsModel.load(self)

    def save_settings(self, settings_model):
        """Save a SettingsModel to persistent storage."""
        settings_model.save(self)
        self.sync()

    @staticmethod
    def _as_bool(value, default=True):
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes", "on")
        if value is None:
            return default
        return bool(value)

    # Theme settings
    def get_theme(self):
        return self.value("theme", "light")

    def set_theme(self, theme_name: str):
        self.setValue("theme", theme_name)

    # Editor font settings
    def get_editor_font_family(self):
        return self.value("editorFontFamily", "Consolas")

    def set_editor_font_family(self, font_family: str):
        self.setValue("editorFontFamily", font_family)

    def get_editor_font_size(self):
        return self.value("editorFontSize", 11, type=int)

    def set_editor_font_size(self, font_size: int):
        self.setValue("editorFontSize", font_size)

    # Sidebar settings
    def get_sidebar_width(self):
        return self.value("sidebarWidth", 300, type=int)

    def set_sidebar_width(self, width: int):
        self.setValue("sidebarWidth", width)

    def get_sidebar_font_size(self):
        return self.value("sidebarFontSize", 10, type=int)

    def set_sidebar_font_size(self, size: int):
        self.setValue("sidebarFontSize", size)

    # Word wrap settings
    def get_word_wrap(self):
        return self._as_bool(self.value("wordWrap", True), True)

    def set_word_wrap(self, enabled: bool):
        self.setValue("wordWrap", enabled)

    # Layout / window state
    def get_sidebar_visible(self):
        return self._as_bool(self.value("sidebarVisible", True), True)

    def set_sidebar_visible(self, visible: bool):
        self.setValue("sidebarVisible", visible)

    def get_status_bar_visible(self):
        return self._as_bool(self.value("statusBarVisible", True), True)

    def set_status_bar_visible(self, visible: bool):
        self.setValue("statusBarVisible", visible)

    def get_preview_visible(self):
        return self._as_bool(self.value("previewVisible", False), False)

    def set_preview_visible(self, visible: bool):
        self.setValue("previewVisible", visible)

    def get_window_geometry(self):
        return self.value("windowGeometry")

    def get_window_state(self):
        return self.value("windowState")

    def get_window_maximized(self):
        return self._as_bool(self.value("windowMaximized", False), False)

    def set_window_maximized(self, maximized: bool):
        self.setValue("windowMaximized", maximized)
