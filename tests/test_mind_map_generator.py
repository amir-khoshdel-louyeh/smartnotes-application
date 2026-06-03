import unittest
from unittest.mock import MagicMock, patch

from services.mind_map_generator import MindMapService, MindMapWorker


class TestMindMapService(unittest.TestCase):
    def tearDown(self):
        MindMapService._generator = None

    @patch("services.mind_map_generator.pipeline")
    def test_get_generator_lazy(self, mock_pipe):
        mock_pipe.return_value = MagicMock()
        g1 = MindMapService.get_generator()
        g2 = MindMapService.get_generator()
        mock_pipe.assert_called_once_with("summarization", model="sshleifer/distilbart-cnn-6-6")
        self.assertIs(g1, g2)

    def test_worker_empty_text(self):
        w = MindMapWorker("   ")
        mock_signals = MagicMock()
        w.signals = mock_signals
        w.run()
        mock_signals.finished.emit.assert_called_once_with("Nothing to map. The editor is empty.")

    @patch("services.mind_map_generator.MindMapService.get_generator")
    def test_worker_success(self, mock_get):
        fake_gen = MagicMock(return_value=[{"summary_text": "First sentence. Second sentence. Third."}])
        mock_get.return_value = fake_gen
        w = MindMapWorker("Some long input text " * 20)
        mock_signals = MagicMock()
        w.signals = mock_signals
        w.run()
        self.assertTrue(mock_signals.finished.emit.called)
        emitted = mock_signals.finished.emit.call_args[0][0]
        self.assertIn("First sentence", emitted)
        self.assertIn("  - Second sentence", emitted)

    @patch("services.mind_map_generator.MindMapService.get_generator", side_effect=RuntimeError("boom"))
    def test_worker_error(self, _mock):
        w = MindMapWorker("hello")
        mock_signals = MagicMock()
        w.signals = mock_signals
        w.run()
        mock_signals.error.emit.assert_called_once()
        self.assertIn("Mind map generation failed", mock_signals.error.emit.call_args[0][0])
