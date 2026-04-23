from transformers import pipeline, Pipeline


class SummarizerService:
    """
    A service to handle text summarization using a pre-trained model.
    Loads the model lazily on the first summarization request.
    """
    _summarizer: Pipeline = None

    @classmethod
    def get_summarizer(cls) -> Pipeline:
        """Lazily loads and returns the summarization pipeline."""
        if cls._summarizer is None:
            cls._summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
        return cls._summarizer

    @classmethod
    def summarize(cls, text: str, length_option: str = "Medium") -> str:
        """Summarize text and return the summary string."""
        if not text.strip():
            raise ValueError("Text is empty.")

        summarizer = cls.get_summarizer()
        text_word_count = len(text.split())
        min_len, max_len = cls.get_summary_lengths(text_word_count)[length_option]
        summary = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False)
        return summary[0]['summary_text']

    @staticmethod
    def get_summary_lengths(text_length: int) -> dict:
        """Calculate min/max lengths for summary based on text length."""
        return {
            "Short": (max(10, int(text_length * 0.1)), max(25, int(text_length * 0.2))),
            "Medium": (max(25, int(text_length * 0.2)), max(75, int(text_length * 0.5))),
            "Long": (max(50, int(text_length * 0.4)), max(150, int(text_length * 0.8))),
        }
