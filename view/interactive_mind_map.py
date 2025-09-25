from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

class InteractiveMindMap(QWidget):
    """
    A custom widget to display an interactive mind map using Matplotlib and NetworkX.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.graph = None
        self.pos = None
        self.is_dark_theme = False
        self.selected_node = None
        self.on_node_select_callback = None

        self.canvas.mpl_connect('pick_event', self.on_pick)

    def set_on_node_select_callback(self, callback):
        self.on_node_select_callback = callback

    def on_pick(self, event):
        """Handle node selection events."""
        if not hasattr(event, 'artist') or not hasattr(event.artist, 'get_label'):
            return

        node_label = event.artist.get_label()
        if node_label in self.graph.nodes:
            self.selected_node = node_label
            self.redraw_graph()
            if self.on_node_select_callback:
                description = self.graph.nodes[self.selected_node].get('description', '')
                self.on_node_select_callback(self.selected_node, description)

    def update_graph(self, graph, is_dark_theme):
        """Update the graph and redraw the canvas."""
        self.graph = graph
        self.is_dark_theme = is_dark_theme
        if self.graph and self.graph.nodes:
            # Re-calculate layout only if the graph changes significantly
            self.pos = nx.spring_layout(self.graph, seed=42)
        else:
            self.pos = None
        self.redraw_graph()

    def redraw_graph(self):
        """Redraws the graph, highlighting the selected node."""
        self.ax.clear()

        if not self.graph or not self.graph.nodes or not self.pos:
            self.ax.text(0.5, 0.5, "Mind map is empty or not generated.", ha='center', va='center')
            self.canvas.draw()
            return

        # Theme colors
        face_color = '#1e1e1e' if self.is_dark_theme else 'white'
        edge_color = '#cccccc' if self.is_dark_theme else '#555555'
        font_color = '#d4d4d4' if self.is_dark_theme else 'black'
        default_node_color = '#007acc'
        selected_node_color = '#ff8c00' # Orange for selection

        self.figure.set_facecolor(face_color)
        self.ax.set_facecolor(face_color)

        # Determine node colors
        node_colors = [selected_node_color if node == self.selected_node else default_node_color for node in self.graph.nodes()]

        # Draw nodes with picker enabled
        nodes = nx.draw_networkx_nodes(self.graph, self.pos, ax=self.ax, node_color=node_colors, node_size=3000)
        if nodes:
            nodes.set_picker(5) # Enable picking on nodes

        # Draw edges and labels
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, edge_color=edge_color, width=1.5, arrows=False)
        nx.draw_networkx_labels(self.graph, self.pos, ax=self.ax, font_size=10, font_color=font_color)

        self.ax.axis('off')
        self.figure.tight_layout(pad=0)
        self.canvas.draw()

    def link_description_to_selected_node(self, description: str):
        """Associates a description with the currently selected node."""
        if self.selected_node and self.selected_node in self.graph.nodes:
            self.graph.nodes[self.selected_node]['description'] = description
            return True
        return False

    def clear(self):
        """Clears the graph and the selection."""
        self.graph = None
        self.selected_node = None
        self.redraw_graph()