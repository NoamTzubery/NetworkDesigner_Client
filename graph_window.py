import sys
import networkx as nx
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QPushButton, QLabel, QGraphicsPixmapItem
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QBrush, QFont, QPixmap


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

    def _get_device_pixmap(self, node_name):
        ln = node_name.lower()
        target = None
        if ln.startswith('computer_'):
            target = 'assets/pc_image.png'
        elif ln.startswith('router_'):
            target = 'assets/router_image.png'
        elif ln.startswith('multilayerswitch'):
            target = 'assets/layer_3_switch_image.png'
        elif ln.startswith('switch_'):
            target = 'assets/switch_image.png'

        if target:
            # load and scale to 55×55
            return QPixmap(target).scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return None

    def draw_layered_topology(self):
        print("[draw_layered_topology] Start")
        sys.stdout.flush()
        if not self.graph or len(self.graph.nodes()) == 0:
            print("[draw_layered_topology] Graph is empty")
            sys.stdout.flush()
            return

        layers = {
            'Access': 0.9,
            'Distribution': 0.6,
            'Core': 0.3
        }
        node_layers = {n: self.graph.nodes[n].get('layer', 'Access') for n in self.graph.nodes()}
        spacing = 150
        pos = {}

        for layer_name, y in layers.items():
            nodes = [n for n, l in node_layers.items() if l == layer_name]
            print(f"[draw_layered_topology] Layer '{layer_name}' has {len(nodes)} nodes")
            sys.stdout.flush()
            for i, n in enumerate(nodes):
                pos[n] = (i * spacing + 50, y * 500)
                print(f"[draw_layered_topology] Node '{n}' position set to {pos[n]}")
                sys.stdout.flush()

        pen = QPen(Qt.white, 2)
        # edges
        for u, v in self.graph.edges():
            if u in pos and v in pos:
                x1, y1 = pos[u]; x2, y2 = pos[v]
                self.scene.addLine(x1, y1, x2, y2, pen)

        # nodes
        for node, (x, y) in pos.items():
            print(f"[draw_layered_topology] Drawing node '{node}' at ({x}, {y})")
            sys.stdout.flush()
            pix = self._get_device_pixmap(node)
            if pix:
                item = QGraphicsPixmapItem(pix)
                item.setOffset(x - pix.width()/2, y - pix.height()/2)
                self.scene.addItem(item)
            else:
                ellipse = QGraphicsEllipseItem(QRectF(x - 15, y - 15, 30, 30))
                ellipse.setBrush(QBrush(Qt.cyan))
                self.scene.addItem(ellipse)

            text = self.scene.addText(node)
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
        node_positions = {n: (x * 400 + 400, y * 400 + 300) for n, (x, y) in pos.items()}
        pen = QPen(Qt.white, 2)

        # edges
        for u, v in self.graph.edges():
            x1, y1 = node_positions[u]; x2, y2 = node_positions[v]
            self.scene.addLine(x1, y1, x2, y2, pen)

        # nodes
        for node, (x, y) in node_positions.items():
            print(f"[draw_standard_topology] Drawing node '{node}' at ({x}, {y})")
            sys.stdout.flush()
            pix = self._get_device_pixmap(node)
            if pix:
                item = QGraphicsPixmapItem(pix)
                item.setOffset(x - pix.width()/2, y - pix.height()/2)
                self.scene.addItem(item)
            else:
                ellipse = QGraphicsEllipseItem(QRectF(x - 10, y - 10, 20, 20))
                ellipse.setBrush(QBrush(Qt.cyan))
                self.scene.addItem(ellipse)

            text = self.scene.addText(node)
            text.setDefaultTextColor(Qt.white)
            text.setPos(x - 15, y - 30)


class VLANTabWindow(QWidget):
    """
    A window with tabs to display each VLAN's graph.
    Each tab shows a QGraphicsView rendering the VLAN's subgraph.
    """

    def __init__(self, vlan_subgraphs, parent=None):
        super().__init__(parent)
        self.vlan_subgraphs = vlan_subgraphs
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
        if not graph or len(graph.nodes()) == 0:
            return

        try:
            pos = nx.spring_layout(graph, seed=42)
        except:
            pos = nx.circular_layout(graph)
        if not pos:
            return

        node_positions = {n: (x * 400 + 400, y * 400 + 300) for n, (x, y) in pos.items()}
        pen = QPen(Qt.white, 2)

        # edges
        for u, v in graph.edges():
            if u in node_positions and v in node_positions:
                x1, y1 = node_positions[u]; x2, y2 = node_positions[v]
                scene.addLine(x1, y1, x2, y2, pen)

        # nodes
        for node, (x, y) in node_positions.items():
            print(f"[VLANTabWindow.draw_graph] Drawing node '{node}' at ({x}, {y})")
            pix = GraphWindow._get_device_pixmap(GraphWindow, node)
            if pix:
                item = QGraphicsPixmapItem(pix)
                item.setOffset(x - pix.width()/2, y - pix.height()/2)
                scene.addItem(item)
            else:
                ellipse = QGraphicsEllipseItem(QRectF(x - 10, y - 10, 20, 20))
                ellipse.setBrush(QBrush(Qt.cyan))
                scene.addItem(ellipse)

            text = scene.addText(node)
            text.setDefaultTextColor(Qt.white)
            text.setPos(x - 15, y - 30)
