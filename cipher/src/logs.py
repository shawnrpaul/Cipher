from __future__ import annotations
from typing import Optional, Type, TYPE_CHECKING
from pathlib import Path
import logging
import traceback
import sys
import os


from PyQt6.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from .window import Window
    from types import TracebackType


__all__ = ("Logs",)


class Stdout:
    def __init__(self, logs: Logs) -> None:
        self.logs = logs

    def write(self, text: str):
        self.logs.setPlainText(f"{self.logs.toPlainText()}{text}")

    def flush(self) -> None:
        ...


class Logs(QPlainTextEdit):
    def __init__(self, window: Window) -> None:
        super().__init__()
        self._window = window
        action = self.addAction("Hide Logs")
        action.setShortcut("Alt+C")
        action.triggered.connect(
            lambda: self.show() if self.isHidden() else self.hide()
        )
        self.window.addAction(action)

        self.scrollbar = self.verticalScrollBar()

        self.setWindowTitle("Log")
        self.resize(700, 350)

        self.setContentsMargins(0, 0, 0, 0)
        self.setReadOnly(True)

        self.stdout = Stdout(self)

    @property
    def window(self) -> Window:
        return self._window

    def log(self, text: str, level=logging.ERROR):
        self.write(text)
        logging.log(msg=text, level=level)

    def setPlainText(self, text: str) -> None:
        value = self.scrollbar.value()
        max = self.scrollbar.maximum()
        super().setPlainText(text)
        self.scrollbar.setValue(self.scrollbar.maximum()) if value != max else ...

    def excepthook(
        self,
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_tb: TracebackType,
    ):
        try:
            file = Path(exc_tb.tb_frame.f_code.co_filename)
            line = exc_tb.tb_lineno
            logging.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
            if file.is_relative_to(os.getcwd()):
                return self.window.application.close()
        except Exception:
            logging.error(f"{exc_type.__name__}: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_tb)
