from transformers import pipeline, Pipeline
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable


class MindMapService(QObject):
    """
    A service to handle mind map generation using a pre-trained model.
    Loads the model lazily on the first request.
    """
    _generator: Pipeline = None

    @classmethod
    def get_generator(cls) -> Pipeline:
        """Lazily loads and returns the text generation pipeline."""
        if cls._generator is None:
            # Using a text generation model to structure the output.
            # This is a small, fast model suitable for this task.
            cls._generator = pipeline("text2text-generation", model="sshleifer/distilbart-cnn-6-6")
        return cls._generator


class MindMapWorker(QRunnable):
    """
    Worker thread for generating a mind map without blocking the GUI.
    """
    class Signals(QObject):
        finished = pyqtSignal(str)
        error = pyqtSignal(str)

    def __init__(self, text: str):
        super().__init__()
        self.text = text
        self.signals = self.Signals()

    def run(self):
        """Perform the mind map generation."""
        try:
            if not self.text.strip():
                self.signals.finished.emit("Nothing to map. The editor is empty.")
                return

            generator = MindMapService.get_generator()
            prompt = f"Generate a hierarchical, indented list of topics and sub-topics from the following text:\n\n{self.text}"
            result = generator(prompt, max_length=150, num_beams=4, early_stopping=True)
            self.signals.finished.emit(result[0]['generated_text'].replace(' - ', '  - ')) # Ensure consistent indentation
        except Exception as e:
            self.signals.error.emit(f"Mind map generation failed: {e}")