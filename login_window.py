import asyncio
import json
import websockets
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from qasync import asyncSlot

from home_window import HomeWindow
from client_window import ClientWindow
from dispatcher import WebSocketDispatcher


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign In / Sign Up")
        self.resize(400, 200)
        self.websocket = None
        self.dispatcher = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_label.setFont(QFont("Segoe UI", 12))
        self.username_input = QLineEdit()
        self.username_input.setFont(QFont("Segoe UI", 12))

        self.password_label = QLabel("Password:")
        self.password_label.setFont(QFont("Segoe UI", 12))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("Segoe UI", 12))

        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.setFont(QFont("Segoe UI", 12))
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setFont(QFont("Segoe UI", 12))

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.signup_button)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.on_login_clicked)
        self.signup_button.clicked.connect(self.on_signup_clicked)

    @asyncSlot()
    async def on_login_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        try:
            self.websocket = await websockets.connect("ws://localhost:6789", ping_interval=None)
            # Create the dispatcher right after connection.
            self.dispatcher = WebSocketDispatcher(self.websocket)
            auth_data = {
                "action": "login",
                "username": username,
                "password": password
            }
            # Use the dispatcher to send the login request and wait for a response.
            response_data = await asyncio.wait_for(self.dispatcher.send_and_wait(auth_data), timeout=2)
            if "error" in response_data:
                QMessageBox.critical(self, "Login Failed", response_data["error"])
                await self.websocket.close()
                return
        except asyncio.TimeoutError:
            # No immediate error; assume login OK.
            pass
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error: {e}")
            return

        # On successful login, open the home window passing the dispatcher.
        self.accept()
        self.home_window = HomeWindow(self.dispatcher)
        self.home_window.show()
        self.close()

    @asyncSlot()
    async def on_signup_clicked(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        try:
            async with websockets.connect("ws://localhost:6789", ping_interval=None) as websocket:
                auth_data = {
                    "action": "signup",
                    "username": username,
                    "password": password
                }
                await websocket.send(json.dumps(auth_data))
                response = await websocket.recv()
                response_data = json.loads(response)
                if "error" in response_data:
                    QMessageBox.critical(self, "Sign Up Failed", response_data["error"])
                else:
                    QMessageBox.information(self, "Sign Up Success", response_data["message"])
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error: {e}")
