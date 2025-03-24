import ipaddress
import json
import networkx as nx
from networkx.readwrite import json_graph

# ** We add Qt here to fix "name 'Qt' is not defined" **
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QComboBox, QGroupBox
)
from PyQt5.QtGui import QFont
from qasync import asyncSlot

from graph_window import GraphWindow, VLANTabWindow
from network_client import send_configuration


class ClientWindow(QWidget):
    """
    Main UI window that collects network configuration input, sends the data to the server,
    displays the response, and allows the user to view the generated graphs.
    """

    def __init__(self, websocket, parent=None):
        super().__init__(parent)
        self.websocket = websocket
        self.access_graph = None
        self.top_graph = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Network Topology Client")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Title Label
        title_label = QLabel("Network Topology Generator")
        title_label.setAlignment(Qt.AlignCenter)  # <-- requires Qt import
        title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        main_layout.addWidget(title_label)

        # Group Box for Network Configuration inputs
        config_group = QGroupBox("Network Configuration")
        config_group.setFont(QFont("Segoe UI", 16, QFont.Bold))
        config_layout = QGridLayout()
        config_layout.setHorizontalSpacing(20)
        config_layout.setVerticalSpacing(15)

        labels_and_fields = [
            ("Number of Routers:", "2"),
            ("Number of MultiLayer Switches:", "2"),
            ("Number of Switches:", "4"),
            ("Number of Computers:", "15"),
            ("Mode (0: Fault-tolerant, 1: Scalable):", "1"),
            ("IP Base (e.g., 192.168.0.0):", "192.168.0.0")
        ]
        self.input_fields = []
        for row, (label_text, placeholder) in enumerate(labels_and_fields):
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 14))
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"default: {placeholder}")
            input_field.setMinimumHeight(40)
            input_field.setFont(QFont("Segoe UI", 14))
            self.input_fields.append(input_field)
            config_layout.addWidget(label, row, 0)
            config_layout.addWidget(input_field, row, 1)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Generate Topology Button
        self.generateButton = QPushButton("Generate Topology")
        self.generateButton.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.generateButton.setMinimumHeight(50)
        main_layout.addWidget(self.generateButton)

        # Graph Visualization Selection
        selection_group = QGroupBox("Graph Visualization")
        selection_group.setFont(QFont("Segoe UI", 16, QFont.Bold))
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(20)

        self.graphSelector = QComboBox()
        self.graphSelector.setFont(QFont("Segoe UI", 14))
        self.graphSelector.addItem("Access Graph")
        self.graphSelector.addItem("Top Graph")
        self.graphSelector.setMinimumHeight(40)

        self.viewGraphButton = QPushButton("View Graph")
        self.viewGraphButton.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.viewGraphButton.setMinimumHeight(50)

        selection_layout.addWidget(self.graphSelector)
        selection_layout.addWidget(self.viewGraphButton)
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # Output Text Area
        output_label = QLabel("Output:")
        output_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_layout.addWidget(output_label)

        self.outputText = QTextEdit()
        self.outputText.setFont(QFont("Segoe UI", 14))
        self.outputText.setReadOnly(True)
        main_layout.addWidget(self.outputText)

        self.setLayout(main_layout)
        self.generateButton.clicked.connect(self.on_generate_clicked)
        self.viewGraphButton.clicked.connect(self.on_view_graph_clicked)
        self.showMaximized()

    def validate_inputs(self):
        try:
            num_routers = int(self.input_fields[0].text()) if self.input_fields[0].text() else 2
            num_mls = int(self.input_fields[1].text()) if self.input_fields[1].text() else 2
            num_switches = int(self.input_fields[2].text()) if self.input_fields[2].text() else 4
            num_computers = int(self.input_fields[3].text()) if self.input_fields[3].text() else 15
            mode = int(self.input_fields[4].text()) if self.input_fields[4].text() else 1
            ip_base = self.input_fields[5].text() if self.input_fields[5].text() else "192.168.0.0"

            if num_routers < 1 or num_mls < 1 or num_switches < 1 or num_computers < 1:
                return False, "All device counts must be at least 1."
            if mode not in (0, 1):
                return False, "Mode must be 0 (fault-tolerant) or 1 (scalable)."
            try:
                ipaddress.IPv4Address(ip_base)
            except ValueError:
                return False, "Invalid IP Base format. Use something like '192.168.0.0'."
            return True, {
                "num_routers": num_routers,
                "num_mls": num_mls,
                "num_switches": num_switches,
                "num_computers": num_computers,
                "mode": mode,
                "ip_base": ip_base
            }
        except ValueError:
            return False, "Invalid input. Please enter only numbers where required."

    @asyncSlot()
    async def on_generate_clicked(self):
        valid, result = self.validate_inputs()
        if not valid:
            self.outputText.append(f"Error: {result}")
            return

        request_data = result
        self.outputText.append("Sending configuration to server...")
        try:
            response = await send_configuration(self.websocket, request_data)
            if "error" in response:
                self.outputText.append("Error from server: " + response["error"])
            else:
                self.outputText.append("Received data from server.")
                self.access_graph = json_graph.node_link_graph(response['access_graph'])
                self.top_graph = json_graph.node_link_graph(response['top_graph'])
                self.outputText.append(
                    f"Graphs received! Nodes: {len(self.access_graph.nodes())} in Access Graph, "
                    f"{len(self.top_graph.nodes())} in Top Graph."
                )
        except Exception as e:
            self.outputText.append("Exception: " + str(e))

    def on_view_graph_clicked(self):
        if self.access_graph is None or self.top_graph is None:
            self.outputText.append("No graph data available. Please generate topology first.")
            return

        selected_graph = self.graphSelector.currentText()
        if selected_graph == "Access Graph":
            vlan_to_nodes = {}
            for node, data in self.access_graph.nodes(data=True):
                vlan = data.get('vlan', 'Default')
                vlan_to_nodes.setdefault(vlan, []).append(node)
            if not vlan_to_nodes:
                self.outputText.append("No VLAN data found in the Access Graph.")
                return
            vlan_subgraphs = {vlan: self.access_graph.subgraph(nodes).copy()
                              for vlan, nodes in vlan_to_nodes.items()}
            self.vlan_tabs_window = VLANTabWindow(vlan_subgraphs)
            self.vlan_tabs_window.show()
        elif selected_graph == "Top Graph":
            self.graph_window = GraphWindow(self.top_graph, "Top Graph", graph_type="top")
            self.graph_window.show()
