"""Recently opened files, persisted through the settings layer."""

import os


class RecentFilesManager:
    """Stores a small MRU list of files in QSettings."""

    KEY = "recentFiles"

    def __init__(self, settings_manager, limit: int = 10):
        self._settings = settings_manager
        self._limit = max(1, limit)

    def files(self) -> list[str]:
        raw = self._settings.value(self.KEY, [])
        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, (list, tuple)):
            raw = []
        return [path for path in raw if isinstance(path, str) and path]

    def add(self, file_path: str | None) -> None:
        if not file_path:
            return
        path = os.path.abspath(file_path)
        if not os.path.isfile(path):
            return
        items = [p for p in self.files() if os.path.normcase(p) != os.path.normcase(path)]
        items.insert(0, path)
        self._settings.setValue(self.KEY, items[: self._limit])
        self._settings.sync()

    def clear(self) -> None:
        self._settings.setValue(self.KEY, [])
        self._settings.sync()
