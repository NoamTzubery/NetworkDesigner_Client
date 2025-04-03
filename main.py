import sys
import asyncio
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from login_window import LoginWindow


def load_stylesheet(file_path):
    with open(file_path, "r") as f:
        return f.read()


def main():
    app = QApplication(sys.argv)

    stylesheet = load_stylesheet("style.qss")
    app.setStyleSheet(stylesheet)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    login_window = LoginWindow()
    login_window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
