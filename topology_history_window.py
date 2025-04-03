import asyncio
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox,
    QHBoxLayout, QTabWidget
)
from PyQt5.QtGui import QFont
from qasync import asyncSlot
import networkx as nx
from networkx.readwrite import json_graph
from graph_window import GraphWindow  # using your existing GraphWindow


class TopologyHistoryWindow(QWidget):
    def __init__(self, websocket, parent=None):
        super().__init__(parent)
        self.websocket = websocket
        self.setWindowTitle("Past Topologies")
        self.resize(600, 400)
        self.topologies = []  # will hold the list of past topologies
        self.initUI()
        # Load the history when the window is created
        asyncio.create_task(self.load_topologies())

    def initUI(self):
        layout = QVBoxLayout()

        # List widget to show topology IDs
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Segoe UI", 12))

        # Buttons for refreshing and viewing details
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFont(QFont("Segoe UI", 12))
        self.view_button = QPushButton("View Selected Topology")
        self.view_button.setFont(QFont("Segoe UI", 12))

        # Connect buttons to actions
        self.refresh_button.clicked.connect(self.load_topologies)
        self.view_button.clicked.connect(self.open_topology_detail)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.view_button)

        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    @asyncSlot()
    async def load_topologies(self):
        """Request and load the user's past topologies from the server."""
        try:
            request_data = {
                "action": "get_history"
            }
            await self.websocket.send(json.dumps(request_data))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            if "error" in response_data:
                QMessageBox.critical(self, "Error", response_data["error"])
                return

            # Expecting the response to have a "graphs" key with the list of topologies
            self.topologies = response_data.get("graphs", [])
            self.populate_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load topologies: {e}")

    def populate_list(self):
        """Fill the list widget with topology IDs."""
        self.list_widget.clear()
        for topo in self.topologies:
            # Display the topology ID (you can include more info if available)
            item_text = f"Topology ID: {topo['id']}"
            self.list_widget.addItem(item_text)

    def open_topology_detail(self):
        """Open a detail view for the selected topology."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a topology from the list.")
            return

        index = self.list_widget.currentRow()
        selected_topology = self.topologies[index]
        self.detail_window = TopologyDetailWindow(selected_topology)
        self.detail_window.show()


class TopologyDetailWindow(QWidget):
    """
    A window that shows detailed graphs for a single topology.
    Displays two tabs: one for the access graph and one for the top graph.
    """

    def __init__(self, topology_data, parent=None):
        super().__init__(parent)
        self.topology_data = topology_data
        self.setWindowTitle(f"Topology Details - {topology_data['id']}")
        self.resize(900, 700)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        try:
            # Convert JSON data back to NetworkX graphs using node-link format
            access_graph = json_graph.node_link_graph(self.topology_data["access_graph"])
            top_graph = json_graph.node_link_graph(self.topology_data["top_graph"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse graph data: {e}")
            return

        # Create a GraphWindow instance for each graph.
        # For the access graph, we pass graph_type "access" (which triggers standard layout).
        access_graph_window = GraphWindow(access_graph, title="Access Graph", graph_type="access")
        top_graph_window = GraphWindow(top_graph, title="Top Graph", graph_type="top")

        # Add each GraphWindow to a separate tab.
        self.tab_widget.addTab(access_graph_window, "Access Graph")
        self.tab_widget.addTab(top_graph_window, "Top Graph")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
