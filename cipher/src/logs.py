from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from .window import Window


__all__ = ("Logs",)


class Logs(QPlainTextEdit):
    def __init__(self, window: Window) -> None:
        super().__init__()
        self._window = window
        self.scrollbar = self.verticalScrollBar()
        self.setContentsMargins(0, 0, 0, 0)
        self.setReadOnly(True)

    @property
    def window(self) -> Window:
        return self._window

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == int(Qt.Key.Key_C):  # fmt: skip
            self.copy()
            return e.accept()
        return super().keyPressEvent(e)

    def setPlainText(self, text: str) -> None:
        value = self.scrollbar.value()
        max = self.scrollbar.maximum()
        super().setPlainText(text)
        self.scrollbar.setValue(self.scrollbar.maximum()) if value != max else ...

    def write(self, text: str):
        self.setPlainText(f"{self.toPlainText()}{text}")

    def log(self, text: str, level=logging.ERROR):
        self.write(text)
        logging.log(msg=text, level=level)
