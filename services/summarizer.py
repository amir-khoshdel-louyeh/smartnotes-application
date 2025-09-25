from transformers import pipeline, Pipeline
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable


class SummarizerService(QObject):
    """
    A service to handle text summarization using a pre-trained model.
    Loads the model lazily on the first summarization request.
    """
    _summarizer: Pipeline = None

    @classmethod
    def get_summarizer(cls) -> Pipeline:
        """Lazily loads and returns the summarization pipeline."""
        if cls._summarizer is None:
            # Using a smaller, faster model for demonstration purposes.
            # For higher quality, consider 'facebook/bart-large-cnn'.
            cls._summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
        return cls._summarizer

    @staticmethod
    def get_summary_lengths(text_length: int) -> dict:
        """Calculate min/max lengths for summary based on text length."""
        return {
            "Short": (max(10, int(text_length * 0.1)), max(25, int(text_length * 0.2))),
            "Medium": (max(25, int(text_length * 0.2)), max(75, int(text_length * 0.5))),
            "Long": (max(50, int(text_length * 0.4)), max(150, int(text_length * 0.8))),
        }


class SummarizationWorker(QRunnable):
    """
    Worker thread for running summarization without blocking the GUI.
    """
    class Signals(QObject):
        finished = pyqtSignal(str)
        error = pyqtSignal(str)

    def __init__(self, text: str, length_option: str):
        super().__init__()
        self.text = text
        self.length_option = length_option
        self.signals = self.Signals()

    def run(self):
        """Perform the summarization."""
        try:
            if not self.text.strip():
                self.signals.finished.emit("Nothing to summarize.")
                return

            summarizer = SummarizerService.get_summarizer()
            text_word_count = len(self.text.split())
            min_len, max_len = SummarizerService.get_summary_lengths(text_word_count)[self.length_option]
            
            summary = summarizer(self.text, max_length=max_len, min_length=min_len, do_sample=False)
            self.signals.finished.emit(summary[0]['summary_text'])
        except Exception as e:
            self.signals.error.emit(f"Summarization failed: {e}")


class PreloadWorker(QRunnable):
    """
    A simple worker to preload the summarizer model in the background.
    """
    def run(self):
        """Trigger the model loading."""
        try:
            SummarizerService.get_summarizer()
        except Exception:
            # Fails silently, the error will be caught during actual use.
            pass