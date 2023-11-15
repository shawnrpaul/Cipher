from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from pathlib import Path
import os
import sys

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget


if TYPE_CHECKING:
    from .window import Window

if sys.platform == "win32":
    defaultPath = Path(os.getenv("USERPROFILE")).absolute()
else:
    defaultPath = Path(os.getenv("HOME")).absolute()

__all__ = ("Terminal",)


class Stdin(QLineEdit):
    def __init__(self, terminal: Terminal) -> None:
        super().__init__(terminal)
        self.terminal = terminal
        self.stdout = terminal.stdout
        self.prevCommands = []
        self.index = 0

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
        elif (
            a0.modifiers() == Qt.KeyboardModifier.ControlModifier
            and key == int(Qt.Key.Key_C)
            and self.terminal.isRunning()
        ):
            self.terminal._process.kill()
            return a0.accept()
        return super().keyPressEvent(a0)

    def returnPressed(self) -> None:
        text = self.text()
        if self.terminal.isRunning():
            self.stdout.setPlainText(f"{self.stdout.toPlainText()}{text}\n")
            self.terminal._process.write(f"{text}\n".encode())
        else:
            self.processCommand(text)
        self.clear()

    def processCommand(self, text: str) -> None:
        command = text.lstrip().lower()
        if command == "clear":
            return self.stdout.setPlainText(f"{self.terminal.currentDirectory}>")
        self.stdout.setPlainText(f"{self.stdout.toPlainText()}{text}\n")
        if command == "ls":
            contents = "    ".join(
                path for path in os.listdir(self.terminal.currentDirectory)
            )
            return self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{contents}\n\n{self.terminal.currentDirectory}>"
            )
        if text.startswith("cd") and len(command := text.rstrip().split(" ")) > 1:
            self.terminal.currentDirectory = (
                self.terminal.currentDirectory.parent
                if command[1] == ".."
                else path
                if (path := Path(command[1]).absolute()).exists()
                else defaultPath
            )
            return self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}\n{self.terminal.currentDirectory}>"
            )
        self.terminal.runProcess(text)


class Terminal(QWidget):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._window = window
        self._process = None

        self.window.onClose.connect(
            lambda: self._process.kill() if self.isRunning() else ...
        )

        self.currentDirectory = self.window.currentFolder
        self.window.fileManager.onWorkspaceChanged.connect(self.changeDirectory)

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

    def isRunning(self) -> bool:
        return bool(self._process)

    def show(self) -> None:
        self.stdin.setFocus()
        return super().show()

    def changeDirectory(self, path: Optional[Path]) -> None:
        self.currentDirectory = path if path else defaultPath
        self.stdout.clear()
        self.stdout.setPlainText(f"{self.currentDirectory}>")

    def stateChanged(self, state: QProcess.ProcessState) -> None:
        if state == QProcess.ProcessState.NotRunning:
            self._process = None
            self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}\n{self.currentDirectory}>"
            )

    def _run(self, program: str, args: list[str], directory: str):
        self.show() if self.isHidden() else ...
        self._process = QProcess(self)
        self._process.setProgram(program)
        self._process.setArguments(args)
        self._process.setWorkingDirectory(directory)
        self._process.stateChanged.connect(self.stateChanged)
        self._process.readyReadStandardOutput.connect(
            lambda: self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{self._process.readAllStandardOutput().data().decode()}"
            )
        )
        self._process.readyReadStandardError.connect(
            lambda: self.stdout.setPlainText(
                f"{self.stdout.toPlainText()}{self._process.readAllStandardError().data().decode()}"
            )
        )
        self._process.start()

    def run(self) -> None:
        if not self._window.currentFolder or self.isRunning():
            return
        if sys.platform == "win32":
            program, args = "powershell", [".cipher\\run.bat"]
        elif sys.platform == "linux":
            program, args = "bash", [".cipher/run.sh"]
        output = f"{program} {' '.join(args)}"
        self.stdout.setPlainText(f"{self.stdout.toPlainText()}{output}\n")
        self.stdin.prevCommands.append(f"{output}")
        self.stdin.index = len(self.stdin.prevCommands)
        self._run(program, args, str(self.currentDirectory))

    def runProcess(self, text: str) -> None:
        if self.isRunning():
            return
        program, *args = text.split(" ")
        self._run(program, args, str(self.currentDirectory))
