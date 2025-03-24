import sys
import networkx as nx
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QBrush, QFont


class GraphWindow(QWidget):
    """
    A window to display a NetworkX graph using a QGraphicsView.
    Can render either a layered (topology) view or a spring-layout view.
    """

    def __init__(self, graph, title="Graph Visualization", graph_type="top", parent=None):
        super().__init__(parent)
        self.graph = graph
        self.graph_type = graph_type  # "top" for layered, "access" for standard layout
        print("[GraphWindow] Initializing with graph_type:", self.graph_type)
        sys.stdout.flush()
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.initUI()

    def initUI(self):
        print("[GraphWindow] initUI() start")
        sys.stdout.flush()
        layout = QVBoxLayout()

        # Title Label
        self.graph_label = QLabel(self.windowTitle(), self)
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setFont(QFont("Segoe UI", 16, QFont.Bold))

        # Graphics view and scene for the graph
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        # Back button to close the graph window
        self.back_button = QPushButton("Back to Home")
        self.back_button.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.back_button.setMinimumHeight(40)
        self.back_button.clicked.connect(self.close)

        layout.addWidget(self.graph_label)
        layout.addWidget(self.view)
        layout.addWidget(self.back_button)
        self.setLayout(layout)
        print("[GraphWindow] UI initialized")
        sys.stdout.flush()

        # Draw graph based on type
        if self.graph_type == "top":
            print("[GraphWindow] Calling draw_layered_topology()")
            sys.stdout.flush()
            self.draw_layered_topology()
        else:
            print("[GraphWindow] Calling draw_standard_topology()")
            sys.stdout.flush()
            self.draw_standard_topology()

    def draw_layered_topology(self):
        print("[draw_layered_topology] Start")
        sys.stdout.flush()
        if not self.graph or len(self.graph.nodes()) == 0:
            print("[draw_layered_topology] Graph is empty")
            sys.stdout.flush()
            return

        # Define layers with y-coordinates (lower values appear higher)
        layers = {
            'Access': 0.9,
            'Distribution': 0.6,
            'Core': 0.3
        }
        # Use node attribute "layer" (default is 'Access')
        node_layers = {node: self.graph.nodes[node].get('layer', 'Access') for node in self.graph.nodes()}
        spacing = 150  # Horizontal spacing
        pos = {}

        for layer_name, y_coord in layers.items():
            nodes_in_layer = [node for node, layer in node_layers.items() if layer == layer_name]
            print(f"[draw_layered_topology] Layer '{layer_name}' has {len(nodes_in_layer)} nodes")
            sys.stdout.flush()
            for i, node in enumerate(nodes_in_layer):
                pos[node] = (i * spacing + 50, y_coord * 500)
                print(f"[draw_layered_topology] Node '{node}' position set to {pos[node]}")
                sys.stdout.flush()

        pen = QPen(Qt.white, 2)
        # Draw edges
        for edge in self.graph.edges():
            node1, node2 = edge
            if node1 in pos and node2 in pos:
                x1, y1 = pos[node1]
                x2, y2 = pos[node2]
                print(
                    f"[draw_layered_topology] Drawing edge from {node1} to {node2} at positions {pos[node1]} and {pos[node2]}")
                sys.stdout.flush()
                self.scene.addLine(x1, y1, x2, y2, pen)

        # Draw nodes and labels
        for node, (x, y) in pos.items():
            print(f"[draw_layered_topology] Drawing node '{node}' at ({x}, {y})")
            sys.stdout.flush()
            ellipse = QGraphicsEllipseItem(QRectF(x - 15, y - 15, 30, 30))
            ellipse.setBrush(QBrush(Qt.cyan))
            self.scene.addItem(ellipse)
            text = self.scene.addText(str(node))
            text.setDefaultTextColor(Qt.white)
            text.setPos(x - 15, y - 30)

    def draw_standard_topology(self):
        print("[draw_standard_topology] Start")
        sys.stdout.flush()
        if not self.graph or len(self.graph.nodes()) == 0:
            print("[draw_standard_topology] Graph is empty")
            sys.stdout.flush()
            return

        pos = nx.spring_layout(self.graph, seed=42)
        node_positions = {
            node: (x * 400 + 400, y * 400 + 300)
            for node, (x, y) in pos.items()
        }
        print(f"[draw_standard_topology] Computed positions for {len(node_positions)} nodes")
        sys.stdout.flush()
        pen = QPen(Qt.white, 2)
        # Draw edges
        for edge in self.graph.edges():
            node1, node2 = edge
            x1, y1 = node_positions[node1]
            x2, y2 = node_positions[node2]
            print(
                f"[draw_standard_topology] Drawing edge from {node1} to {node2} at positions {node_positions[node1]} and {node_positions[node2]}")
            sys.stdout.flush()
            self.scene.addLine(x1, y1, x2, y2, pen)

        # Draw nodes and labels
        for node, (x, y) in node_positions.items():
            print(f"[draw_standard_topology] Drawing node '{node}' at ({x}, {y})")
            sys.stdout.flush()
            ellipse = QGraphicsEllipseItem(QRectF(x - 10, y - 10, 20, 20))
            ellipse.setBrush(QBrush(Qt.cyan))
            self.scene.addItem(ellipse)
            text = self.scene.addText(str(node))
            text.setDefaultTextColor(Qt.white)
            text.setPos(x - 15, y - 30)


class VLANTabWindow(QWidget):
    """
    A window with tabs to display each VLAN's graph.
    Each tab shows a QGraphicsView rendering the VLAN's subgraph.
    """

    def __init__(self, vlan_subgraphs, parent=None):
        super().__init__(parent)
        self.vlan_subgraphs = vlan_subgraphs  # Dictionary: {vlan_id: subgraph}
        print("[VLANTabWindow] Initializing with", len(self.vlan_subgraphs), "subgraphs")
        self.setWindowTitle("Access Graph VLANs")
        self.resize(900, 700)
        self.initUI()

    def initUI(self):
        print("[VLANTabWindow] initUI() start")
        layout = QVBoxLayout()
        self.tabWidget = QTabWidget()
        layout.addWidget(self.tabWidget)

        for vlan, subgraph in self.vlan_subgraphs.items():
            print(f"[VLANTabWindow] Creating tab for VLAN '{vlan}' with {len(subgraph.nodes())} nodes")
            tab = QWidget()
            tab_layout = QVBoxLayout()

            # Create a QGraphicsScene and QGraphicsView for this VLAN
            scene = QGraphicsScene()
            view = QGraphicsView(scene)
            self.draw_graph(scene, subgraph)

            tab_layout.addWidget(view)
            tab.setLayout(tab_layout)
            self.tabWidget.addTab(tab, f"VLAN: {vlan}")

        self.setLayout(layout)
        self.tabWidget.setStyleSheet("QTabBar::tab { color: black; }")
        print("[VLANTabWindow] UI initialized")

    def draw_graph(self, scene, graph):
        print("[VLANTabWindow.draw_graph] Start for graph with", len(graph.nodes()), "nodes")
        print("[VLANTabWindow.draw_graph] Nodes:", list(graph.nodes()))
        print("[VLANTabWindow.draw_graph] Edges:", list(graph.edges()))
        if not graph or len(graph.nodes()) == 0:
            print("[VLANTabWindow.draw_graph] Graph is empty")
            return

        # Try computing positions using spring_layout.
        try:
            pos = nx.spring_layout(graph, seed=42)
            print("[VLANTabWindow.draw_graph] spring_layout computed successfully")
        except Exception as e:
            print("[VLANTabWindow.draw_graph] Exception in spring_layout:", e)
            try:
                pos = nx.circular_layout(graph)
                print("[VLANTabWindow.draw_graph] circular_layout computed successfully")
            except Exception as e2:
                print("[VLANTabWindow.draw_graph] Exception in circular_layout:", e2)
                # Fallback: manual circular layout without numpy.
                pos = {}
                n = len(graph.nodes())
                if n == 0:
                    print("[VLANTabWindow.draw_graph] No nodes to layout manually")
                else:
                    angle_step = 2 * math.pi / n
                    for i, node in enumerate(graph.nodes()):
                        pos[node] = (math.cos(i * angle_step), math.sin(i * angle_step))
                    print("[VLANTabWindow.draw_graph] Falling back to manual circular layout:", pos)

        # Verify that positions were computed.
        if not pos or len(pos) == 0:
            print("[VLANTabWindow.draw_graph] Failed to compute positions for nodes!")
            return

        # Scale and shift positions to match our view.
        node_positions = {
            node: (x * 400 + 400, y * 400 + 300)
            for node, (x, y) in pos.items()
        }
        print("[VLANTabWindow.draw_graph] Node positions:", node_positions)

        pen = QPen(Qt.white, 2)
        # Draw edges.
        for edge in graph.edges():
            node1, node2 = edge
            if node1 in node_positions and node2 in node_positions:
                x1, y1 = node_positions[node1]
                x2, y2 = node_positions[node2]
                print(
                    f"[VLANTabWindow.draw_graph] Drawing edge from {node1} to {node2} at positions {node_positions[node1]} and {node_positions[node2]}")
                scene.addLine(x1, y1, x2, y2, pen)
        # Draw nodes and labels.
        for node, (x, y) in node_positions.items():
            print(f"[VLANTabWindow.draw_graph] Drawing node '{node}' at ({x}, {y})")
            ellipse = QGraphicsEllipseItem(QRectF(x - 10, y - 10, 20, 20))
            ellipse.setBrush(QBrush(Qt.cyan))
            scene.addItem(ellipse)
            text = scene.addText(str(node))
            text.setDefaultTextColor(Qt.white)
            text.setPos(x - 15, y - 30)
