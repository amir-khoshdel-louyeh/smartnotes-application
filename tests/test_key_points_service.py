import unittest
from unittest.mock import MagicMock, patch

from services.key_points_extractor import KeyPointsService


class TestKeyPointsService(unittest.TestCase):
    def tearDown(self):
        KeyPointsService._extractor = None

    @patch("services.key_points_extractor.pipeline")
    def test_extract_key_points_returns_formatted_list(self, mock_pipeline):
        fake_extractor = MagicMock()
        fake_extractor.return_value = [
            {"word": "important", "score": 0.95, "entity": "B-KEY"},
            {"word": "other", "score": 0.50, "entity": "I-KEY"},
        ]
        mock_pipeline.return_value = fake_extractor

        result = KeyPointsService.extract_key_points("Some text with a key point.")

        self.assertEqual(result, "- important (Score: 0.95)")
        mock_pipeline.assert_called_once_with("token-classification", model="ml6team/keyphrase-extraction-kbir-inspec")

    def test_extract_key_points_empty_text_raises_value_error(self):
        with self.assertRaises(ValueError):
            KeyPointsService.extract_key_points("\n   \t")

    @patch("services.key_points_extractor.pipeline")
    def test_extract_key_points_returns_no_points_message(self, mock_pipeline):
        fake_extractor = MagicMock()
        fake_extractor.return_value = [
            {"word": "nothing", "score": 0.1, "entity": "O"}
        ]
        mock_pipeline.return_value = fake_extractor

        result = KeyPointsService.extract_key_points("This is a sample sentence.")

        self.assertEqual(result, "No key points found.")
