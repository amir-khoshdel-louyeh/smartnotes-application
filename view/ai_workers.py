from PyQt5.QtCore import QObject, pyqtSignal, QRunnable
from services.summarizer import SummarizerService
from services.key_points_extractor import KeyPointsService


class AIWorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)


class SummarizationWorker(QRunnable):
    """Worker thread for running summarization without blocking the GUI."""

    def __init__(self, text: str, length_option: str):
        super().__init__()
        self.text = text
        self.length_option = length_option
        self.signals = AIWorkerSignals()

    def run(self):
        try:
            summary = SummarizerService.summarize(self.text, self.length_option)
            self.signals.finished.emit(summary)
        except Exception as e:
            self.signals.error.emit(f"Summarization failed: {e}")


class KeyPointsWorker(QRunnable):
    """Worker thread for extracting key points without blocking the GUI."""

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.signals = AIWorkerSignals()

    def run(self):
        try:
            key_points_text = KeyPointsService.extract_key_points(self.text)
            self.signals.finished.emit(key_points_text)
        except Exception as e:
            self.signals.error.emit(f"Key points extraction failed: {e}")


class PreloadWorker(QRunnable):
    """Worker to preload AI models in the background."""

    def run(self):
        try:
            SummarizerService.get_summarizer()
            KeyPointsService.get_extractor()
        except Exception:
            pass
