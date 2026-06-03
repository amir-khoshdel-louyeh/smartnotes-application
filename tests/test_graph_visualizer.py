import unittest
from unittest.mock import MagicMock, patch

from services.graph_visualizer import parse_indented_text, create_mind_map_pixmap  # noqa: E402


class TestGraphVisualizer(unittest.TestCase):
    def test_parse_empty_returns_empty_graph(self):
        g = parse_indented_text("")
        self.assertEqual(len(g.nodes), 0)
        self.assertEqual(len(g.edges), 0)

    def test_parse_single_node(self):
        g = parse_indented_text("Root")
        self.assertIn("Root", g.nodes)
        self.assertEqual(len(g.edges), 0)

    def test_parse_hierarchy(self):
        text = "Root\n  - A\n    - B\n  - C"
        g = parse_indented_text(text)
        self.assertEqual(set(g.nodes), {"Root", "- A", "- B", "- C"})
        self.assertIn(("Root", "- A"), g.edges)
        self.assertIn(("- A", "- B"), g.edges)
        self.assertIn(("Root", "- C"), g.edges)

    def test_parse_sibling_flat_indent(self):
        g = parse_indented_text("Root\n- A\n- B")
        self.assertIn(("Root", "- A"), g.edges)
        self.assertIn(("Root", "- B"), g.edges)

    def test_parse_prunes_deeper_levels(self):
        g = parse_indented_text("Root\n  - A\n  - B\n    - C\n    - D")
        self.assertIn(("Root", "- B"), g.edges)
        self.assertIn(("- B", "- C"), g.edges)
        self.assertIn(("- B", "- D"), g.edges)

    def test_create_pixmap_empty(self):
        g = parse_indented_text("")
        with patch("services.graph_visualizer.QPixmap") as mock_pix:
            mock_inst = MagicMock()
            mock_pix.return_value = mock_inst
            result = create_mind_map_pixmap(g, False)
            self.assertIs(result, mock_inst)

    def test_create_pixmap_renders(self):
        g = parse_indented_text("Root\n  - A\n  - B")
        with patch("services.graph_visualizer.QPixmap") as mock_pix, \
             patch("services.graph_visualizer.nx.spring_layout", return_value={"Root": (0, 0), "- A": (1, 0), "- B": (0, 1)}), \
             patch("services.graph_visualizer.nx.draw"), \
             patch("services.graph_visualizer.plt") as mock_plt:
            mock_plt.gca.return_value.set_facecolor = MagicMock()
            mock_inst = MagicMock()
            mock_inst.isNull.return_value = False
            mock_pix.return_value = mock_inst
            mock_inst.loadFromData.return_value = True
            result = create_mind_map_pixmap(g, True)
            self.assertIs(result, mock_inst)
            mock_plt.figure.assert_called_once()
            mock_plt.savefig.assert_called_once()
            mock_plt.close.assert_called_once()
