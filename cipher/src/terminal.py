from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from enum import Enum
from pathlib import Path
import sys
import os

from PyQt6.QtCore import QProcess, QProcessEnvironment, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget


if TYPE_CHECKING:
    from .window import Window


class ShellType(Enum):
    Powershell = 0
    Bash = 1


if sys.platform == "win32":
    defaultPath = Path(os.getenv("USERPROFILE")).absolute()
    shell = ShellType.Powershell
else:
    defaultPath = Path(os.getenv("HOME")).absolute()
    shell = ShellType.Bash

__all__ = ("Terminal",)


class Process(QProcess):
    def __init__(self, terminal: Terminal) -> None:
        super().__init__()
        self.terminal = terminal
        self.readyReadStandardOutput.connect(self.dataRecieved)
        self.readyReadStandardError.connect(self.errorRecieved)
        self.createProcess(self.terminal.window.currentFolder)

    def createProcess(self, path: Optional[Path]) -> None:
        match shell:
            case ShellType.Powershell:
                self.setProgram("powershell")
                self.setArguments(["-nologo"])
            case ShellType.Bash:
                self.setProgram("bash")
        self.setWorkingDirectory(str(path) if path else str(defaultPath))
        env = QProcessEnvironment()
        env.insert(env.systemEnvironment())
        env.insert("PYTHONUNBUFFERED", "True")
        self.setProcessEnvironment(env)
        self.start()

    @property
    def stdout(self) -> QPlainTextEdit:
        return self.terminal.stdout

    def changeDirectory(self, path: Optional[Path]) -> None:
        self.kill()
        self.stdout.clear()
        self.createProcess(path)

    def readAll(self) -> str:
        return super().readAll().data().decode()

    def readAllStandardOutput(self) -> str:
        return super().readAllStandardOutput().data().decode()

    def readAllStandardError(self) -> str:
        return super().readAllStandardError().data().decode()

    def dataRecieved(self) -> None:
        data = self.readAllStandardOutput()
        if data.startswith("clear\n"):
            self.stdout.clear()
            data = data.split("\n")[1]
        self.stdout.setPlainText(f"{self.stdout.toPlainText()}{data}")

    def errorRecieved(self) -> None:
        self.stdout.setPlainText(
            f"{self.stdout.toPlainText()}{self.readAllStandardError()}"
        )

    def kill(self) -> None:
        super().kill()
        self.waitForFinished()


class Stdin(QLineEdit):
    def __init__(self, terminal: Terminal) -> None:
        super().__init__(terminal)
        self.terminal = terminal
        self.prevCommands = []
        self.index = 0

    @property
    def stdout(self) -> QPlainTextEdit:
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
        elif a0.modifiers() == Qt.KeyboardModifier.ControlModifier and key == int(
            Qt.Key.Key_C
        ):
            self.terminal._process.write("Ctrl+C\n".encode())
            return a0.accept()
        return super().keyPressEvent(a0)

    def returnPressed(self) -> None:
        text = self.text()
        self.terminal._process.write(f"{text}\n".encode())
        self.clear()


class Terminal(QWidget):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._window = window
        self._process = Process(self)

        self.window.fileManager.onWorkspaceChanged.connect(
            self._process.changeDirectory
        )
        self.window.onClose.connect(self._process.close)

        self.stdout = QPlainTextEdit(self)
        self.stdout.setReadOnly(True)
        self.stdin = Stdin(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stdout)
        layout.addWidget(self.stdin)
        self.setLayout(layout)

        self.hide()

    @property
    def window(self) -> Window:
        return self._window

    def show(self) -> None:
        self.stdin.setFocus()
        return super().show()
