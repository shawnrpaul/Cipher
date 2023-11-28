from __future__ import annotations
from pathlib import Path
import asyncio
import logging
import sys
import os
import io

from psutil import process_iter
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser, QFileSystemWatcher
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
import requests
import zipfile

from cipher.src import Window
from .server import Server
from .client import Client

__all__ = ("Application", "ServerApplication")


class Application(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.setApplicationDisplayName("Cipher")
        self.setApplicationName("Cipher")
        self.setApplicationVersion("1.3.2")
        self._background_tasks: list[asyncio.Task] = []
        self.isRunning = False

    @staticmethod
    def getApplication() -> Application:
        processes = tuple(process.name() for process in process_iter())
        if processes.count("Cipher.exe") > 1:
            return ClientApplication(sys.argv)
        return ServerApplication(sys.argv)

    async def eventLoop(self):
        while self.isRunning:
            self.processEvents()
            await asyncio.sleep(1e-4)

    def _taskFinished(self, task: asyncio.Task) -> None:
        self._background_tasks.remove(task)

    def createTask(self, coro) -> asyncio.Task:
        task = self.loop.create_task(coro)
        task.add_done_callback(self._taskFinished)
        self._background_tasks.append(task)
        return task

    def start(self) -> None:
        if not self.isRunning:
            self.isRunning = True
            self.loop.create_task(self.eventLoop())
            try:
                self.loop.run_forever()
            except KeyboardInterrupt:
                self.close()
            finally:
                self.loop.run_until_complete(asyncio.sleep(0.5))

    def close(self):
        self.quit()
        self.isRunning = False
        for task in self._background_tasks:
            task.cancel()
        self.loop.stop() if self.loop.is_running() else ...


class ClientApplication(Application):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.client = Client(self)
        self.start()


class ServerApplication(Application):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setWindowIcon(QIcon(f"{self.localAppData}/icons/window.png"))
        self.server = Server(self)
        styles = f"{self.localAppData}/styles/styles.qss"
        self._styles = QFileSystemWatcher(self)
        self._styles.addPath(styles)
        self._styles.fileChanged.connect(
            lambda: self.setStyleSheet(open(styles).read())
        )
        self.setStyleSheet(open(styles).read())
        self._shortcut = QFileSystemWatcher(
            [f"{self.localAppData}/shortcuts.json"], self
        )

        self.windows: list[Window] = []
        self.parseArgs(argv)

    @property
    def localAppData(self) -> str:
        if not hasattr(self, "_localAppData"):
            if sys.platform == "win32":
                _env = os.getenv("LocalAppData")
                self._localAppData = os.path.join(_env, "Cipher")
            elif sys.platform == "linux":
                _env = os.getenv("HOME")
                self._localAppData = os.path.join(_env, "Cipher")
            else:
                raise NotADirectoryError("MacOS isn't Supported")

            if not os.path.exists(self._localAppData):
                req = requests.get(
                    "https://github.com/Srpboyz/Cipher/releases/latest/download/LocalAppData.zip"
                )
                req.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(req.content)) as zip_file:
                    zip_file.extractall(_env)

            sys.path.insert(0, f"{self._localAppData}/include")
            sys.path.insert(0, f"{self._localAppData}/site-packages")

            logging.basicConfig(
                filename=f"{self._localAppData}/logs.log",
                format="%(levelname)s:%(asctime)s: %(message)s",
                level=logging.ERROR,
            )
        return self._localAppData

    def parseArgs(self, argv: list[str]):
        parser = QCommandLineParser()
        parser.addHelpOption()

        new = QCommandLineOption(["n", "new-window"], "Use a new window")
        parser.addOption(new)

        parser.process(argv)

        args = parser.positionalArguments()

        if args:
            val = args[0]
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
