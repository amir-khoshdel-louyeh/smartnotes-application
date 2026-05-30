try:
    from transformers import pipeline, Pipeline
except ImportError:  # transformers not installed in lightweight envs
    pipeline = None
    Pipeline = object  # type: ignore

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable


class MindMapService(QObject):
    """
    A service to handle mind map generation using a pre-trained model.
    Loads the model lazily on the first request.
    """
    _generator = None

    @classmethod
    def get_generator(cls):
        """Lazily loads and returns the summarization pipeline for structuring."""
        if cls._generator is None:
            _pipeline = pipeline
            if _pipeline is None:
                from transformers import pipeline as _pipeline  # type: ignore
            # Re-use summarization model (text2text with same checkpoint is invalid)
            cls._generator = _pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
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

            # Truncate to avoid token limit; produce hierarchical list via summarizer
            max_words = 600
            words = self.text.split()
            truncated = " ".join(words[:max_words]) if len(words) > max_words else self.text
            generator = MindMapService.get_generator()
            # Summarize then convert sentences to indented list fallback if model doesn't support hierarchy
            result = generator(truncated, max_length=130, min_length=30, do_sample=False, truncation=True)
            raw = result[0].get('summary_text', '') or result[0].get('generated_text', '')
            # Turn sentences into indented bullet list for graph_visualizer
            sentences = [s.strip() for s in raw.split('.') if s.strip()]
            if not sentences:
                self.signals.finished.emit(raw)
                return
            lines = [sentences[0]]
            for s in sentences[1:]:
                lines.append(f"  - {s}")
            self.signals.finished.emit("\n".join(lines))
        except Exception as e:
            self.signals.error.emit(f"Mind map generation failed: {e}")
