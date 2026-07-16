"""Non-blocking GitHub release check (kept off the GUI thread)."""

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal

DEFAULT_REPO = "smartnotes-application/smartnotes-application"


class UpdateCheckSignals(QObject):
    finished = pyqtSignal(str, str)  # tag, html_url
    error = pyqtSignal(str)


class UpdateCheckWorker(QRunnable):
    """Queries the GitHub releases API without freezing the interface."""

    def __init__(self, repo: str = DEFAULT_REPO, timeout: int = 6):
        super().__init__()
        self.repo = repo
        self.timeout = timeout
        self.signals = UpdateCheckSignals()

    def run(self) -> None:
        try:
            import requests

            response = requests.get(
                f"https://api.github.com/repos/{self.repo}/releases/latest",
                timeout=self.timeout,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "StudyMate"},
            )
            if response.status_code != 200:
                raise RuntimeError(f"GitHub returned HTTP {response.status_code}")
            payload = response.json()
            tag = payload.get("tag_name", "unknown")
            url = payload.get("html_url", f"https://github.com/{self.repo}/releases")
            self.signals.finished.emit(tag, url)
        except Exception as exc:  # noqa: BLE001 - reported in the UI
            self.signals.error.emit(str(exc))
