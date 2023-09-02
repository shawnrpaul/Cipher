import os
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Optional, Type

from PyQt6.QtWidgets import QApplication

from cipher.src.window import MainWindow, logger


def excepthook(func: Callable[..., Any], app: QApplication) -> Any:
    def log(
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
        return func(exc_type, exc_value, exc_tb)

    return log


def run() -> None:
    app = QApplication([])
    window = MainWindow()
    sys.excepthook = excepthook(sys.excepthook, app)
    app.aboutToQuit.connect(window.close)
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()


if __name__ == "__main__":
    run()
