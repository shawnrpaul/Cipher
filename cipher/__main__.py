from PyQt6.QtWidgets import QApplication
from cipher import MainWindow


def run() -> None:
    app = QApplication([])
    window = MainWindow()
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()


if __name__ == "__main__":
    run()
