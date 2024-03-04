from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit


if TYPE_CHECKING:
    from . import Terminal
    from .stdout import Stdout


class Stdin(QLineEdit):
    def __init__(self, terminal: Terminal) -> None:
        super().__init__(terminal)
        self.terminal = terminal
        self.prevCommands = []
        self.index = 0

    @property
    def stdout(self) -> Stdout:
        return self.terminal.stdout

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        key = a0.key()
        if key == int(Qt.Key.Key_Return):
            self.prevCommands.append(self.text())
            self.index = len(self.prevCommands)
            self.returnPressed()
            return a0.accept()
        elif key == int(Qt.Key.Key_Up):
            length = len(self.prevCommands)
            if length > 0:
                self.index = index if (index := self.index - 1) >= 0 else self.index
                self.setText(self.prevCommands[self.index])
                return a0.accept()
        elif key == int(Qt.Key.Key_Down):
            length = len(self.prevCommands)
            if length > 0:
                if (index := self.index + 1) < length:
                    self.index = index
                    self.setText(self.prevCommands[self.index])
                else:
                    self.clear()
                return a0.accept()
        elif a0.modifiers() == Qt.KeyboardModifier.ControlModifier and key == int(Qt.Key.Key_C):  # fmt: skip
            self.terminal._process.write("\\x03\n".encode())
            return a0.accept()
        return super().keyPressEvent(a0)

    def returnPressed(self) -> None:
        text = self.text()
        self.terminal._process.write(f"{text}\n".encode())
        self.clear()
