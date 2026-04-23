import unittest
from unittest.mock import MagicMock, patch

from services.summarizer import SummarizerService


class TestSummarizerService(unittest.TestCase):
    def tearDown(self):
        SummarizerService._summarizer = None

    @patch("services.summarizer.pipeline")
    def test_summarize_returns_summary(self, mock_pipeline):
        fake_summarizer = MagicMock()
        fake_summarizer.return_value = [{"summary_text": "test summary"}]
        mock_pipeline.return_value = fake_summarizer

        summary = SummarizerService.summarize("This is a long enough text to summarize.", "Short")

        self.assertEqual(summary, "test summary")
        mock_pipeline.assert_called_once_with("summarization", model="sshleifer/distilbart-cnn-6-6")

    def test_summarize_empty_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            SummarizerService.summarize("   ", "Medium")

    def test_get_summary_lengths_returns_expected_keys(self):
        lengths = SummarizerService.get_summary_lengths(100)

        self.assertIn("Short", lengths)
        self.assertIn("Medium", lengths)
        self.assertIn("Long", lengths)
        self.assertEqual(lengths["Short"], (10, 25))
