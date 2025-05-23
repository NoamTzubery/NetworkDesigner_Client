import asyncio
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QMessageBox, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
from qasync import asyncSlot
from networkx.readwrite import json_graph
from graph_window import GraphWindow, VLANTabWindow
from home_window import HomeWindow
from config_window import ConfigWindow


class TopologyHistoryWindow(QWidget):
    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self.selected_topology = None
        self.topologies = []
        self.initUI()
        print("[HistoryWindow] Initialized.")
        # Schedule start_loading after a short delay to ensure the widget is fully set up.
        QTimer.singleShot(100, self.start_loading)

    def start_loading(self):
        print("[HistoryWindow] start_loading() called.")
        try:
            asyncio.create_task(self.load_topologies())
        except Exception as e:
            print("[HistoryWindow] Exception in start_loading:", e)

    def initUI(self):
        self.setWindowTitle("Past Topologies - Full Screen")
        self.showFullScreen()  # Make the window full screen

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top section: Return to Home button and topology list
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.return_home_button = QPushButton("Return to Home")
        self.return_home_button.setFont(QFont("Segoe UI", 14))
        self.return_home_button.clicked.connect(self.return_to_home)

        top_layout.addWidget(self.return_home_button)
        # The refresh button is removed from here

        self.topology_list = QListWidget()
        self.topology_list.setFont(QFont("Segoe UI", 12))
        self.topology_list.itemSelectionChanged.connect(self.on_topology_selected)

        # Layout for top section (buttons + list)
        top_section_layout = QVBoxLayout()
        top_section_layout.addLayout(top_layout)
        top_section_layout.addWidget(self.topology_list)

        # Middle section: A frame that will hold the graph view
        self.graph_frame = QFrame()
        self.graph_frame.setFrameShape(QFrame.StyledPanel)
        self.graph_frame_layout = QVBoxLayout()
        self.graph_frame.setLayout(self.graph_frame_layout)

        # Bottom section: Buttons to view Access Graph, Top Graph, and Configuration
        bottom_layout = QHBoxLayout()
        self.view_access_button = QPushButton("View Access Graph")
        self.view_access_button.setFont(QFont("Segoe UI", 14))
        self.view_top_button = QPushButton("View Top Graph")
        self.view_top_button.setFont(QFont("Segoe UI", 14))
        self.view_config_button = QPushButton("View Configuration")
        self.view_config_button.setFont(QFont("Segoe UI", 14))
        self.view_access_button.clicked.connect(self.view_access_graph)
        self.view_top_button.clicked.connect(self.view_top_graph)
        self.view_config_button.clicked.connect(self.view_configuration)
        bottom_layout.addWidget(self.view_access_button)
        bottom_layout.addWidget(self.view_top_button)
        bottom_layout.addWidget(self.view_config_button)

        main_layout.addLayout(top_section_layout)
        # Let the graph_frame expand
        main_layout.addWidget(self.graph_frame, stretch=1)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)
        print("[HistoryWindow] UI set up.")

    @asyncSlot()
    async def load_topologies(self):
        print("[HistoryWindow] load_topologies() called.")
        # Clear any currently displayed graph view
        self.clear_graph_view()
        try:
            request_data = {"action": "get_history"}
            print("[HistoryWindow] Sending request:", request_data)
            response_data = await self.dispatcher.send_and_wait(request_data)
            print("[HistoryWindow] Received response:", response_data)
            if "error" in response_data:
                QMessageBox.critical(self, "Error", response_data["error"])
                return
            self.topologies = response_data.get("graphs", [])
            print("[HistoryWindow] Loaded topologies:", self.topologies)
            self.populate_list()
            # Now that topologies are loaded, you can access the configurations
            for topo in self.topologies:
                access_config = topo.get("access_configuration")
                top_config = topo.get("top_layer_configurations")
                print(f"[HistoryWindow] Topology ID: {topo['id']}")
                print(f"[HistoryWindow]   Access Configuration: {access_config}")
                print(f"[HistoryWindow]   Top Configuration: {top_config}")
                # In a future step, you might want to store these configurations
                # in self.topologies or a separate data structure for later use.
        except Exception as e:
            print("[HistoryWindow] Exception in load_topologies:", e)
            QMessageBox.critical(self, "Error", f"Failed to load topologies: {e}")

    def populate_list(self):
        print("[HistoryWindow] Populating topology list.")
        self.topology_list.clear()
        for topo in self.topologies:
            item_text = f"Topology ID: {topo['id']}"
            self.topology_list.addItem(item_text)
        print("[HistoryWindow] List populated with", len(self.topologies), "items.")

    def on_topology_selected(self):
        selected_items = self.topology_list.selectedItems()
        if selected_items:
            index = self.topology_list.currentRow()
            self.selected_topology = self.topologies[index]
            print("[HistoryWindow] Selected topology:", self.selected_topology)
        else:
            self.selected_topology = None

    def clear_graph_view(self):
        print("[HistoryWindow] Clearing graph view.")
        # Remove and delete all widgets from the graph frame layout.
        while self.graph_frame_layout.count():
            child = self.graph_frame_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def view_access_graph(self):
        if not self.selected_topology:
            QMessageBox.warning(self, "Selection Error", "Please select a topology from the list.")
            return
        self.clear_graph_view()
        try:
            print("[HistoryWindow] Parsing access graph data...")
            access_graph = json_graph.node_link_graph(self.selected_topology["access_graph"])
            print("[HistoryWindow] Access graph parsed successfully.")
        except Exception as e:
            print("[HistoryWindow] Error parsing access graph:", e)
            QMessageBox.critical(self, "Error", f"Failed to parse access graph: {e}")
            return

        # Group nodes by VLAN (defaulting to 'Default' if not set)
        vlan_to_nodes = {}
        for node, data in access_graph.nodes(data=True):
            vlan = data.get('vlan', 'Default')
            vlan_to_nodes.setdefault(vlan, []).append(node)

        if not vlan_to_nodes:
            QMessageBox.information(self, "No VLAN Data", "No VLAN data found in the Access Graph.")
            return

        # Create subgraphs for each VLAN
        vlan_subgraphs = {vlan: access_graph.subgraph(nodes).copy() for vlan, nodes in vlan_to_nodes.items()}

        # Create the VLANTabWindow widget and add it to the graph frame layout
        vlan_tabs_widget = VLANTabWindow(vlan_subgraphs)
        self.graph_frame_layout.addWidget(vlan_tabs_widget)
        print("[HistoryWindow] Access graph with VLAN tabs displayed.")

    def view_top_graph(self):
        if not self.selected_topology:
            QMessageBox.warning(self, "Selection Error", "Please select a topology from the list.")
            return
        self.clear_graph_view()
        try:
            print("[HistoryWindow] Parsing top graph data...")
            top_graph = json_graph.node_link_graph(self.selected_topology["top_graph"])
            print("[HistoryWindow] Top graph parsed successfully.")
        except Exception as e:
            print("[HistoryWindow] Error parsing top graph:", e)
            QMessageBox.critical(self, "Error", f"Failed to parse top graph: {e}")
            return
        graph_widget = GraphWindow(top_graph, title="Top Graph", graph_type="top")
        self.graph_frame_layout.addWidget(graph_widget)
        print("[HistoryWindow] Top graph displayed.")

    def view_configuration(self):
        if not self.selected_topology:
            QMessageBox.warning(self, "Selection Error", "Please select a topology from the list.")
            return

        access_config = self.selected_topology.get("access_configuration", [])
        top_config = self.selected_topology.get("top_layer_configurations", [])

        self.config_window = ConfigWindow(access_config, top_config)
        self.config_window.show()
        print("[HistoryWindow] Configuration window opened.")

    def return_to_home(self):
        # Instantiate and show the HomeWindow, then close this window.
        self.home_window = HomeWindow(self.dispatcher)
        self.home_window.show()
        self.close()