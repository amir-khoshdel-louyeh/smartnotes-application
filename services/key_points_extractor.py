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


class OnlineKeyPointsWorker(QRunnable):
    """
    Worker thread for running key points extraction via an online API.
    """
    class Signals(QObject):
        finished = pyqtSignal(str)
        error = pyqtSignal(str)

    def __init__(self, text: str, api_key: str):
        super().__init__()
        self.text = text
        self.api_key = api_key
        self.signals = self.Signals()

    def run(self):
        """Perform key points extraction using an online API."""
        if not self.api_key:
            self.signals.error.emit("API key is not set. Please add it in Settings.")
            return

        # --- This is a placeholder for a real API call ---
        api_url = "https://api.example.com/extract_keywords"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"text": self.text}

        try:
            # response = requests.post(api_url, json=payload, headers=headers)
            # response.raise_for_status()
            # key_points = response.json()['keywords'] # Assuming API returns a list of keywords
            # formatted_points = "\n".join([f"- {kp}" for kp in key_points])
            # self.signals.finished.emit(formatted_points)
            self.signals.error.emit("Online key points extraction is not implemented yet. This is a placeholder. Please edit services/key_points_extractor.py.")
        except Exception as e:
            self.signals.error.emit(f"Online key points extraction failed: {e}")