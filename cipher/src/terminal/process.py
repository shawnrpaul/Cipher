from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
from pathlib import Path
import sys
import os

from PyQt6.QtCore import pyqtSignal, QProcess, QProcessEnvironment

if TYPE_CHECKING:
    from . import Terminal
    from .stdout import Stdout
    from ..window import Window


class ShellType(Enum):
    Powershell = 0
    Bash = 1


if sys.platform == "win32":
    defaultPath = Path(os.getenv("USERPROFILE")).absolute()
    shell = ShellType.Powershell
else:
    defaultPath = Path(os.getenv("HOME")).absolute()
    shell = ShellType.Bash


class Process(QProcess):
    newProcess = pyqtSignal()

    def __init__(self, terminal: Terminal) -> None:
        super().__init__()
        self.terminal = terminal
        self.readyReadStandardOutput.connect(self.dataRecieved)
        self.readyReadStandardError.connect(self.errorRecieved)
        self.createProcess(self.window.currentFolder)

    @property
    def window(self) -> Window:
        return self.terminal.window

    @property
    def stdout(self) -> Stdout:
        return self.terminal.stdout

    def createProcess(self, path: Path | None) -> None:
        match shell:
            case ShellType.Powershell:
                self.setProgram("powershell")
                self.setArguments(["-nologo"])
            case ShellType.Bash:
                self.setProgram("bash")
        self.setWorkingDirectory(str(path) if path else str(defaultPath))
        env = QProcessEnvironment()
        env.insert(env.systemEnvironment())
        self.setProcessEnvironment(env)
        self.start()
        self.newProcess.emit()

    def changeDirectory(self, path: Path | None) -> None:
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

    def run(self) -> None:
        match shell:
            case ShellType.Powershell:
                path = Path(f"{self.window.currentFolder}/.cipher/run.bat\n")
            case ShellType.Bash:
                path = Path(f"{self.window.currentFolder}/.cipher/run.sh\n")
        self.write(str(path).encode())

    def kill(self) -> None:
        super().kill()
        self.waitForFinished()
