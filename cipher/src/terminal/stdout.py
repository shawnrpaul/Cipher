from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from . import Terminal


class Stdout(QPlainTextEdit):
    def __init__(self, terminal: Terminal) -> None:
        super().__init__(terminal)
        self.scrollbar = self.verticalScrollBar()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == int(Qt.Key.Key_C):  # fmt: skip
            self.copy()
            return e.accept()
        return super().keyPressEvent(e)

    def setPlainText(self, text: str) -> None:
        value = self.scrollbar.value()
        max = self.scrollbar.maximum()
        super().setPlainText(text)
        if value == max:
            self.scrollbar.setValue(self.scrollbar.maximum())
