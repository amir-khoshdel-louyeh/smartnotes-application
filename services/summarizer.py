
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

class SummarizerService:
    """
    A service to handle text summarization using a pre-trained model.
    Loads the model lazily on the first summarization request.
    """
    _summarizer = None

    @classmethod
    def get_summarizer(cls):
        """Lazily loads and returns the summarization pipeline."""
        if cls._summarizer is None:
            if pipeline is None:
                from transformers import pipeline as _pipeline
            else:
                _pipeline = pipeline
            cls._summarizer = _pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
        return cls._summarizer

    @classmethod
    def summarize(cls, text: str, length_option: str = "Medium") -> str:
        """Summarize text and return the summary string."""
        if not text.strip():
            raise ValueError("Text is empty.")

        summarizer = cls.get_summarizer()
        # Chunk long texts to respect model's token limit (~1024 tokens ≈ 750 words)
        max_chunk_words = 600
        words = text.split()
        if len(words) > max_chunk_words:
            chunks = [" ".join(words[i:i + max_chunk_words]) for i in range(0, len(words), max_chunk_words)]
            summaries = []
            for chunk in chunks:
                chunk_wc = len(chunk.split())
                min_len, max_len = cls.get_summary_lengths(chunk_wc)[length_option]
                # Clamp to model's hard limits to avoid warnings
                max_len = min(max_len, 150)
                min_len = min(min_len, max_len - 5)
                result = summarizer(chunk, max_length=max_len, min_length=min_len, do_sample=False, truncation=True)
                summaries.append(result[0]['summary_text'])
            return "\n\n".join(summaries)

        text_word_count = len(words)
        min_len, max_len = cls.get_summary_lengths(text_word_count)[length_option]
        max_len = min(max_len, 150)
        min_len = min(min_len, max_len - 5)
        summary = summarizer(text, max_length=max_len, min_length=min_len, do_sample=False, truncation=True)
        return summary[0]['summary_text']

    @staticmethod
    def get_summary_lengths(text_length: int) -> dict:
        """Calculate min/max lengths for summary based on text length."""
        return {
            "Short": (max(10, int(text_length * 0.1)), max(25, int(text_length * 0.2))),
            "Medium": (max(25, int(text_length * 0.2)), max(75, int(text_length * 0.5))),
            "Long": (max(50, int(text_length * 0.4)), max(150, int(text_length * 0.8))),
        }
