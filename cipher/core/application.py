from __future__ import annotations
from typing import List
from pathlib import Path
import asyncio
import sys

from psutil import process_iter
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser
from PyQt6.QtWidgets import QApplication
from cipher.src import Window
from .server import Server
from .client import Client

__all__ = ("Application", "ServerApplication")


class Application(QApplication):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.isRunning = False

    @staticmethod
    def getApplication() -> Application:
        processes = tuple(process.name() for process in process_iter())
        if processes.count("python.exe") > 12:
            return ClientApplication(sys.argv)
        return ServerApplication(sys.argv)

    async def eventLoop(self):
        while self.isRunning:
            self.processEvents()
            await asyncio.sleep(0)

    def start(self) -> None:
        if not self.isRunning:
            self.isRunning = True
            asyncio.get_event_loop().run_until_complete(self.eventLoop())

    def close(self):
        self.quit()
        self.isRunning = False


class ClientApplication(Application):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.client = Client(self)
        self.start()


class ServerApplication(Application):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.server = Server(self)
        self.windows: list[Window] = []
        self.parseArgs(argv)

    def parseArgs(self, argv: List[str]):
        parser = QCommandLineParser()
        parser.addHelpOption()

        _path = QCommandLineOption(["p", "path"], "Open a specific path", "path")
        parser.addOption(_path)
        new = QCommandLineOption(["n", "new-window"], "Use a new window")
        parser.addOption(new)

        parser.process(argv)

        if parser.isSet(_path):
            val = parser.value(_path)
            if not (path := Path(val).absolute()).exists():
                msg = f"Path {val} doesn't exist"
                if self.isRunning:
                    return self.server.sendResponse({"code": 400, "message": msg})
                print(msg, file=sys.stderr)
                sys.exit(1)

            if parser.isSet(new) or not self.windows:
                window = self.createWindow()
            else:
                window = self.mainWindow()
            if path.is_dir():
                if not window.currentFolder:
                    window.fileManager.changeFolder(str(path))
            else:
                window.tabView.createTab(path)
            self.server.sendResponse({"code": 200})
            return self.start()

        if self.isRunning:
            self.createWindow()
            return self.server.sendResponse({"code": 200})

        window = self.mainWindow()
        window.resumeSession()
        self.start()

    def createWindow(self) -> Window:
        window = Window(self)
        window.setMainWindow(True) if not self.windows else ...
        self.windows.append(window)
        return window

    def mainWindow(self) -> Window:
        if not self.windows:
            window = Window(self)
            window.setMainWindow(True)
            self.windows.append(window)
        return self.windows[0]

    def closeWindow(self, window: Window):
        self.windows.remove(window)
        if window.isMainWindow():
            if not self.windows:
                return self.close()
            self.windows[0].setMainWindow(True)
