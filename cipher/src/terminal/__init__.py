from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout

from .process import Process
from .stdin import Stdin
from .stdout import Stdout

if TYPE_CHECKING:
    from cipher import Window


__all__ = ("Terminal",)


class Terminal(QFrame):
    newProcess = pyqtSignal()

    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._process = Process(self)
        self._process.newProcess.connect(self.newProcess.emit)

        self.window.fileManager.workspaceChanged.connect(self._process.changeDirectory)
        self.window.closed.connect(self._process.close)

        self.stdout = Stdout(self)
        self.stdout.setReadOnly(True)
        self.stdin = Stdin(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stdout)
        layout.addWidget(self.stdin)
        self.setLayout(layout)

    @property
    def window(self) -> Window:
        return super().window()

    def run(self) -> None:
        self._process.run()
