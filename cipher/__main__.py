from PyQt6.QtWidgets import QApplication
from cipher import MainWindow
import sys


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()


if __name__ == "__main__":
    run()
