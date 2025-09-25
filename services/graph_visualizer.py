import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
from PyQt5.QtGui import QPixmap

def parse_indented_text(text: str):
    """
    Parses indented text into a graph structure.
    Returns a networkx DiGraph.
    """
    graph = nx.DiGraph()
    lines = [line for line in text.split('\n') if line.strip()]
    if not lines:
        return graph

    # The first line is the root
    root_node = lines[0].strip()
    graph.add_node(root_node)

    # Path from root to current node
    path = {0: root_node}

    for line in lines[1:]:
        indentation = len(line) - len(line.lstrip(' '))
        node_name = line.strip()

        # Find the parent in the path based on indentation
        parent_indent = max(i for i in path if i < indentation)
        parent_node = path[parent_indent]

        graph.add_node(node_name)
        graph.add_edge(parent_node, node_name)

        # Update the path
        path[indentation] = node_name

    return graph

def create_mind_map_pixmap(graph: nx.DiGraph, is_dark_theme: bool) -> QPixmap:
    """
    Creates a QPixmap of the mind map graph using matplotlib.
    """
    if not graph.nodes:
        return QPixmap()

    face_color = '#1e1e1e' if is_dark_theme else 'white'
    node_color = '#007acc'
    edge_color = '#cccccc' if is_dark_theme else '#555555'
    font_color = '#d4d4d4' if is_dark_theme else 'black'

    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(8, 6), facecolor=face_color)
    nx.draw(graph, pos, with_labels=True, node_size=3000, node_color=node_color, font_size=10, font_color=font_color, edge_color=edge_color, width=1.5, arrows=False)
    plt.gca().set_facecolor(face_color)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1, facecolor=face_color)
    plt.close()
    buf.seek(0)

    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), 'PNG')
    return pixmap