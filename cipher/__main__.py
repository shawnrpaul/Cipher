from cipher.core import Application
from cipher import MainWindow

import sys


def run() -> None:
    app = Application(sys.argv)
    window = MainWindow()
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.start()


if __name__ == "__main__":
    run()
