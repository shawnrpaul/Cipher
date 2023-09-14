import os
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Type

from PyQt6.QtWidgets import QApplication

from cipher.src.window import MainWindow, logger


def excepthook(
    app: QApplication,
    exc_type: Type[BaseException],
    exc_value: Optional[BaseException],
    exc_tb: TracebackType,
) -> Any:
    tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
    cwd = Path(os.path.dirname(os.path.dirname(__file__))).absolute()
    try:
        for frame in tb.stack[::-1]:
            file = Path(frame.filename).absolute()
            if file.is_relative_to(cwd):
                line = frame.lineno
                break
        logger.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
    except Exception:
        logger.error(f"{exc_type.__name__}: {exc_value}")
    app.quit()
    return sys.__excepthook__(exc_type, exc_value, exc_tb)


def run() -> None:
    app = QApplication([])
    sys.excepthook = lambda *args, **kwargs: excepthook(app, *args, **kwargs)
    window = MainWindow()
    app.aboutToQuit.connect(window.close)
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()


if __name__ == "__main__":
    run()
