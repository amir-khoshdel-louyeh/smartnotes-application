from transformers import pipeline, Pipeline
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable


class KeyPointsService(QObject):
    """
    A service to handle key points extraction using a pre-trained model.
    Loads the model lazily on the first request.
    """
    _extractor: Pipeline = None

    @classmethod
    def get_extractor(cls) -> Pipeline:
        """Lazily loads and returns the token classification pipeline for keyword extraction."""
        if cls._extractor is None:
            # Using a model fine-tuned for keyword extraction.
            cls._extractor = pipeline("token-classification", model="ml6team/keyphrase-extraction-kbir-inspec")
        return cls._extractor


class KeyPointsWorker(QRunnable):
    """
    Worker thread for running key points extraction without blocking the GUI.
    """
    class Signals(QObject):
        finished = pyqtSignal(str)
        error = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.signals = self.Signals()

    def run(self):
        """Perform the key points extraction."""
        try:
            extractor = KeyPointsService.get_extractor()
            key_points = extractor(self.text)
            # Process and format the output
            processed_points = [f"- {point['word']} (Score: {point['score']:.2f})" for point in key_points if point['entity'] == 'B-KEY']
            self.signals.finished.emit("\n".join(processed_points) if processed_points else "No key points found.")
        except Exception as e:
            self.signals.error.emit(f"Key points extraction failed: {e}")