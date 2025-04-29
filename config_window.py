from PyQt5.QtWidgets import (
    QWidget, QListWidget, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QApplication
)
import sys
import json


class ConfigWindow(QWidget):
    def __init__(self, access_configuration, top_layer_configurations):
        super().__init__()
        self.setWindowTitle("Device Configuration")
        self.resize(800, 600)

        # Combine configurations into a dictionary keyed by device name
        self.device_configs = {
            conf['name']: conf
            for conf in (access_configuration + top_layer_configurations)
        }

        self.init_ui()

    def init_ui(self):
        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left side: device list and Show Config button
        left_layout = QVBoxLayout()
        self.device_list = QListWidget()
        self.device_list.addItems(self.device_configs.keys())
        left_layout.addWidget(self.device_list)
        self.show_config_btn = QPushButton("Show Config")
        self.show_config_btn.clicked.connect(self.show_config)
        left_layout.addWidget(self.show_config_btn)

        # Right side: configuration display and Send Configuration button
        right_layout = QVBoxLayout()
        self.config_display = QTextEdit()
        self.config_display.setReadOnly(True)
        right_layout.addWidget(self.config_display)
        self.send_config_btn = QPushButton("Send Configuration")
        self.send_config_btn.clicked.connect(self.send_config)
        right_layout.addWidget(self.send_config_btn)

        # Assemble layouts
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def show_config(self):
        # Display selected device's configuration
        items = self.device_list.selectedItems()
        if not items:
            return
        name = items[0].text()
        conf = self.device_configs.get(name, {})
        self.config_display.setText(json.dumps(conf, indent=4))

    def send_config(self):
        # Placeholder for sending configuration
        # to do: implement sending logic
        pass


if __name__ == "__main__":
    # Example data; replace with actual lists
    access_conf = [
        {"name": "Access_1", "ip_address": "192.168.0.1", "subnet_mask": "255.255.255.0"},
        {"name": "Access_2", "ip_address": "192.168.0.2", "subnet_mask": "255.255.255.0"}
    ]
    top_conf = [
        {"name": "Dist_1", "ip_address": "192.168.1.1", "connections_count": 5},
        {"name": "Core_1", "ip_address": "192.168.1.2", "connections_count": 2}
    ]

    app = QApplication(sys.argv)
    # Load and apply QSS stylesheet
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Warning: Could not load style.qss: {e}")

    window = ConfigWindow(access_conf, top_conf)
    window.show()
    sys.exit(app.exec_())
