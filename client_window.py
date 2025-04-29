import ipaddress
import json
import networkx as nx
from networkx.readwrite import json_graph

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QComboBox, QGroupBox
)
from PyQt5.QtGui import QFont
from qasync import asyncSlot

from graph_window import GraphWindow, VLANTabWindow
from network_client import send_configuration
from home_window import HomeWindow
from config_window import ConfigWindow


class ClientWindow(QWidget):
    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self.access_graph = None
        self.top_graph = None
        self.access_configuration = None
        self.top_layer_configurations = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Network Topology Client")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # — Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        self.returnHomeButton = QPushButton("⇐")
        self.returnHomeButton.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.returnHomeButton.setFixedSize(60, 40)
        self.returnHomeButton.setCursor(Qt.PointingHandCursor)
        self.returnHomeButton.clicked.connect(self.on_return_home_clicked)

        title_label = QLabel("Network Topology Generator")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        header_layout.addWidget(self.returnHomeButton)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # — Input form
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
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 14))
            fld = QLineEdit()
            fld.setPlaceholderText(f"default: {placeholder}")
            fld.setMinimumHeight(40)
            fld.setFont(QFont("Segoe UI", 14))
            self.input_fields.append(fld)
            config_layout.addWidget(lbl, row, 0)
            config_layout.addWidget(fld, row, 1)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # — Generate button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.generateButton = QPushButton("Generate Topology")
        self.generateButton.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.generateButton.setMinimumHeight(50)
        self.generateButton.setSizePolicy(
            self.generateButton.sizePolicy().Expanding,
            self.generateButton.sizePolicy().Preferred
        )
        btn_layout.addWidget(self.generateButton)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # — Graph selection
        selection_group = QGroupBox("Graph Visualization")
        selection_group.setFont(QFont("Segoe UI", 16, QFont.Bold))
        selection_layout = QHBoxLayout()
        self.graphSelector = QComboBox()
        self.graphSelector.setFont(QFont("Segoe UI", 14))
        self.graphSelector.addItems(["Access Graph", "Top Graph"])
        self.graphSelector.setMinimumHeight(40)
        self.viewGraphButton = QPushButton("View Graph")
        self.viewGraphButton.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.viewGraphButton.setMinimumHeight(50)
        selection_layout.addWidget(self.graphSelector)
        selection_layout.addWidget(self.viewGraphButton)
        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # — Show Config button
        cfg_btn_layout = QHBoxLayout()
        cfg_btn_layout.addStretch()
        self.showConfigButton = QPushButton("Show Configuration")
        self.showConfigButton.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.showConfigButton.setMinimumHeight(50)
        self.showConfigButton.setCursor(Qt.PointingHandCursor)
        cfg_btn_layout.addWidget(self.showConfigButton)
        cfg_btn_layout.addStretch()
        main_layout.addLayout(cfg_btn_layout)

        # — Output area
        output_label = QLabel("Output:")
        output_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        main_layout.addWidget(output_label)
        self.outputText = QTextEdit()
        self.outputText.setFont(QFont("Segoe UI", 14))
        self.outputText.setReadOnly(True)
        main_layout.addWidget(self.outputText)

        # — Finalize
        self.setLayout(main_layout)
        self.generateButton.clicked.connect(self.on_generate_clicked)
        self.viewGraphButton.clicked.connect(self.on_view_graph_clicked)
        self.showConfigButton.clicked.connect(self.on_show_config_clicked)
        self.showMaximized()

    def on_return_home_clicked(self):
        home = HomeWindow(self.dispatcher)
        home.show()
        self.close()

    def validate_inputs(self):
        try:
            # parse with defaults
            vals = []
            defaults = [2,2,4,15,1]
            for i in range(5):
                txt = self.input_fields[i].text()
                vals.append(int(txt) if txt else defaults[i])
            ipb = self.input_fields[5].text() or "192.168.0.0"
            if min(vals) < 1 or vals[4] not in (0,1):
                return False, "Check your device counts and mode."
            try:
                ipaddress.IPv4Address(ipb)
            except ValueError:
                return False, "Invalid IP Base format."
            keys = ["num_routers","num_mls","num_switches","num_computers","mode"]
            return True, dict(zip(keys, vals)) | {"ip_base": ipb}
        except ValueError:
            return False, "Please enter valid integers."

    @asyncSlot()
    async def on_generate_clicked(self):
        valid, result = self.validate_inputs()
        if not valid:
            return self.outputText.append(f"Error: {result}")
        request_data = {**result, "action":"create_graph"}
        self.outputText.append("Sending configuration to server...")
        try:
            response = await send_configuration(self.dispatcher, request_data)
            if "error" in response:
                return self.outputText.append("Error from server: " + response["error"])
            # parse graphs
            self.access_graph = json_graph.node_link_graph(response['access_graph'])
            self.top_graph    = json_graph.node_link_graph(response['top_graph'])
            # store configs
            self.access_configuration     = response.get('access_configuration', [])
            self.top_layer_configurations = response.get('top_layer_configurations', [])
            # summary
            self.outputText.append(
                f"Graphs received! Access nodes: {len(self.access_graph)}, "
                f"Top nodes: {len(self.top_graph)}."
            )
            # dump configs
            for label, cfg in [("Access Configuration", self.access_configuration),
                               ("Top-Layer Configuration", self.top_layer_configurations)]:
                self.outputText.append(f"{label}:")
                if isinstance(cfg, list):
                    for i, entry in enumerate(cfg,1):
                        self.outputText.append(f"  [{i}] {entry!r}")
                elif isinstance(cfg, dict):
                    for k,v in cfg.items():
                        self.outputText.append(f"  • {k}: {v!r}")
                else:
                    self.outputText.append(f"  {cfg!r}")
        except Exception as e:
            self.outputText.append("Exception: " + str(e))

    def on_view_graph_clicked(self):
        if not self.access_graph or not self.top_graph:
            return self.outputText.append("No graph data available.")
        if self.graphSelector.currentText() == "Access Graph":
            vlan_to_nodes = {}
            for node,data in self.access_graph.nodes(data=True):
                vlan_to_nodes.setdefault(data.get('vlan','Default'),[]).append(node)
            if not vlan_to_nodes:
                return self.outputText.append("No VLAN data in Access Graph.")
            subgraphs = {v: self.access_graph.subgraph(nodes).copy()
                         for v,nodes in vlan_to_nodes.items()}
            self.vlan_tabs_window = VLANTabWindow(subgraphs)
            self.vlan_tabs_window.show()
        else:
            self.graph_window = GraphWindow(self.top_graph, "Top Graph", graph_type="top")
            self.graph_window.show()

    def on_show_config_clicked(self):
        if not self.access_configuration or not self.top_layer_configurations:
            return self.outputText.append("No configuration data. Generate first.")
        self.config_window = ConfigWindow(
            self.access_configuration,
            self.top_layer_configurations
        )
        self.config_window.show()
