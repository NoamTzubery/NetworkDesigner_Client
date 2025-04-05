from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class HomeWindow(QWidget):
    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self.setWindowTitle("Home")
        self.resize(500, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Welcome to Network Topology Manager")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        self.create_button = QPushButton("Create New Topology")
        self.create_button.setFont(QFont("Segoe UI", 14))
        self.create_button.clicked.connect(self.open_create_topology)

        self.show_button = QPushButton("Show Existing Topologies")
        self.show_button.setFont(QFont("Segoe UI", 14))
        self.show_button.clicked.connect(self.open_show_topologies)

        layout.addWidget(title)
        layout.addSpacing(30)
        layout.addWidget(self.create_button)
        layout.addWidget(self.show_button)

        self.setLayout(layout)

    def open_create_topology(self):
        from client_window import ClientWindow
        self.client_window = ClientWindow(self.dispatcher)
        self.client_window.show()
        self.hide()

    def open_show_topologies(self):
        from topology_history_window import TopologyHistoryWindow
        self.history_window = TopologyHistoryWindow(self.dispatcher)
        self.history_window.show()
        self.hide()
