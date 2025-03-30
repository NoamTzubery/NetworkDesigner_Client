import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from login_window import LoginWindow


def main():
    app = QApplication(sys.argv)

    # Apply dark theme styles
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 4px;
            padding: 8px;
            color: #d4d4d4;
        }
        QPushButton {
            background-color: #0e639c;
            border: none;
            border-radius: 4px;
            padding: 12px 24px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1177bb;
        }
        QLabel {
            font-size: 16px;
        }
        QGroupBox {
            border: 2px solid #3c3c3c;
            border-radius: 5px;
            margin-top: 20px;
            padding: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 4px 6px;
            background-color: #1e1e1e;
        }
    """)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Start with the login window
    login_window = LoginWindow()
    login_window.show()

    with loop:
        loop.run_forever()



if __name__ == "__main__":
    main()
