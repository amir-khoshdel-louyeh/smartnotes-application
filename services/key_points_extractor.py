from transformers import pipeline, Pipeline


class KeyPointsService:
    """
    A service to handle key points extraction using a pre-trained model.
    Loads the model lazily on the first request.
    """
    _extractor: Pipeline = None

    @classmethod
    def get_extractor(cls) -> Pipeline:
        """Lazily loads and returns the token classification pipeline for keyword extraction."""
        if cls._extractor is None:
            cls._extractor = pipeline("token-classification", model="ml6team/keyphrase-extraction-kbir-inspec")
        return cls._extractor

    @classmethod
    def extract_key_points(cls, text: str) -> str:
        """Extract key points from text and return a formatted string."""
        if not text.strip():
            raise ValueError("Text is empty.")

        extractor = cls.get_extractor()
        key_points = extractor(text)
        processed_points = [f"- {point['word']} (Score: {point['score']:.2f})" for point in key_points if point.get('entity') == 'B-KEY']
        return "\n".join(processed_points) if processed_points else "No key points found."
