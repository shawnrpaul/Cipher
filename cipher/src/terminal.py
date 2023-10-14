from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget


if TYPE_CHECKING:
    from .window import MainWindow


class Terminal(QWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._process = None

        self.stdout = QPlainTextEdit(self)
        self.stdout.setReadOnly(True)

        self.stdin = QLineEdit(self)
        self.stdin.returnPressed.connect(self.returnPressed)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stdout)
        layout.addWidget(self.stdin)

        self.setLayout(layout)

        self.hide()

    def isRunning(self) -> bool:
        return bool(self._process)

    def returnPressed(self) -> None:
        if not (text := self.stdin.text()):
            return
        if self.isRunning():
            self.stdout.setPlainText(f"{self.stdout.toPlainText()}{text}\n")
            self._process.write(f"{text}\n".encode())
        else:
            self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{self._window.currentFolder}>{text}\n"
            )
            self.runProcess(text)
        self.stdin.clear()

    def stateChanged(self, state: QProcess.ProcessState) -> None:
        if state == QProcess.ProcessState.NotRunning:
            self._process = None

    def run(self) -> None:
        if not self._window.currentFolder or self.isRunning():
            return
        self.show() if self.isHidden() else ...
        self._process = QProcess(self)
        self._process.setWorkingDirectory(str(self._window.currentFolder))
        self._process.setProgram("powershell")
        self._process.setArguments([".cipher/run.bat"])
        self._process.stateChanged.connect(self.stateChanged)
        self._process.readyRead.connect(
            lambda: self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{self._process.readAll().data().decode()}"
            )
        )
        self._process.start()

    def runProcess(self, text: str) -> None:
        if not self._window.currentFolder or self.isRunning():
            return
        self.show() if self.isHidden() else ...
        program, *args = text.split(" ")
        self._process = QProcess(self)
        self._process.setWorkingDirectory(str(self._window.currentFolder))
        self._process.setProgram(program)
        self._process.setArguments(args)
        self._process.stateChanged.connect(self.stateChanged)
        self._process.readyRead.connect(
            lambda: self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{self._process.readAll().data().decode()}"
            )
        )
        self._process.start()
