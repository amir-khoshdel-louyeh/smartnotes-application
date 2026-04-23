from dataclasses import dataclass
from view.settings_manager import SettingsManager


@dataclass
class SettingsModel:
    theme: str = "light"
    editor_font_family: str = "Consolas"
    editor_font_size: int = 11
    sidebar_width: int = 300
    sidebar_font_size: int = 10
    word_wrap: bool = True

    @classmethod
    def load(cls, manager: SettingsManager) -> "SettingsModel":
        return cls(
            theme=manager.get_theme(),
            editor_font_family=manager.get_editor_font_family(),
            editor_font_size=manager.get_editor_font_size(),
            sidebar_width=manager.get_sidebar_width(),
            sidebar_font_size=manager.get_sidebar_font_size(),
            word_wrap=manager.get_word_wrap(),
        )

    def save(self, manager: SettingsManager) -> None:
        manager.set_theme(self.theme)
        manager.set_editor_font_family(self.editor_font_family)
        manager.set_editor_font_size(self.editor_font_size)
        manager.set_sidebar_width(self.sidebar_width)
        manager.set_sidebar_font_size(self.sidebar_font_size)
        manager.set_word_wrap(self.word_wrap)
        manager.sync()

    def update_theme(self, theme_name: str) -> None:
        self.theme = theme_name

    def update_editor_font_family(self, font_family: str) -> None:
        self.editor_font_family = font_family

    def update_editor_font_size(self, font_size: int) -> None:
        self.editor_font_size = font_size

    def update_sidebar_width(self, width: int) -> None:
        self.sidebar_width = width

    def update_sidebar_font_size(self, size: int) -> None:
        self.sidebar_font_size = size

    def update_word_wrap(self, enabled: bool) -> None:
        self.word_wrap = enabled
