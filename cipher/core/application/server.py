from __future__ import annotations
from types import TracebackType
from typing import Type
from pathlib import Path
import logging
import traceback
import asyncio
import json
import sys
import os

from PyQt6.QtCore import QCommandLineParser, QCommandLineOption, QFileSystemWatcher
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QHostAddress
from PyQt6.QtWebSockets import QWebSocketServer
from PyQt6.QtWidgets import QMessageBox

from cipher.src import Window
from .base import BaseApplication


class Stdout:
    def __init__(self, app: ServerApplication) -> None:
        self.application = app

    def write(self, text: str):
        for window in self.application._windows:
            window.logs.write(text)

    def flush(self) -> None: ...


class PortError(Exception):
    def __init__(self, port: int) -> None:
        super().__init__(f"Port {port} is already in use")


class Server(QWebSocketServer):
    def __init__(self, app: ServerApplication) -> None:
        super().__init__("Cipher Server", QWebSocketServer.SslMode.NonSecureMode, app)
        self.client = None

    @property
    def application(self) -> ServerApplication:
        return self.parent()

    app = application

    def listen(self) -> None:
        if not super().listen(QHostAddress.SpecialAddress.LocalHost, 6969):
            raise PortError(6969)
        self.newConnection.connect(self.onNewConnection)
        self.closed.connect(self.application.exit)
        self.client = None

    def onNewConnection(self) -> None:
        self.client = self.nextPendingConnection()
        self.client.textMessageReceived.connect(self.processTextMessage)
        self.client.disconnected.connect(self.socketDisconnected)

    def processTextMessage(self, message: str) -> None:
        if not self.client:
            return
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return self.sendResponse(
                {"code": 404, "message": "Recieved data isn't in JSON format"}
            )

        if not isinstance(data, dict):
            return self.sendResponse(
                {"code": 404, "message": "Data must be a dictionary"}
            )

        if data.get("code") == 0:
            if argv := data.get("argv"):
                self.application.parseArgs(argv)

    def sendResponse(self, data: dict):
        if not self.client:
            return
        self.client.sendTextMessage(json.dumps(data))
        self.client.disconnect()

    def socketDisconnected(self):
        if self.client:
            self.client.deleteLater()
        self.client = None


class ServerApplication(BaseApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setWindowIcon(QIcon(f"{self.localAppData}/icons/window.png"))

        self._background_tasks: list[asyncio.Task] = []
        self._isRunning = False
        self._isClosing = False

        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

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

        self._windows: list[Window] = []
        sys.stdout = sys.stderr = Stdout(self)
        sys.excepthook = self.excepthook

    @property
    def isRunning(self) -> bool:
        return self._isRunning

    @property
    def isClosing(self) -> bool:
        return self._isClosing

    def parseArgs(self, argv: list[str]):
        if self._isClosing:
            return self.server.sendResponse({"code": 401})
        parser = QCommandLineParser()
        parser.addHelpOption()

        new = QCommandLineOption(["n", "new-window"], "Use a new window")

        parser.addOption(new)
        parser.process(argv)

        if args := parser.positionalArguments():
            val = args[0]
            if not (path := Path(val).absolute()).exists():
                msg = f"Path {val} doesn't exist"
                if self.isRunning:
                    return self.server.sendResponse({"code": 400, "message": msg})
                print(msg, file=sys.stderr)
                self.exit(1)

            if parser.isSet(new) or not self._windows:
                window = self.createWindow()
            else:
                window = self.mainWindow
            if path.is_dir():
                if not window.currentFolder:
                    window.fileManager.changeFolder(path)
            else:
                window.tabView.createTab(path)
            return self.server.sendResponse({"code": 200})

        if self.isRunning:
            self.createWindow()
            return self.server.sendResponse({"code": 200})

        window = self.mainWindow
        window.resumeSession()

    async def runEventLoop(self):
        while self.isRunning:
            self.processEvents()
            await asyncio.sleep(1e-4)
        self.loop.stop() if self.loop.is_running() else ...

    def _taskFinished(self, task: asyncio.Task) -> None:
        self._background_tasks.remove(task)

    def createTask(self, coro) -> asyncio.Task:
        if self.isClosing:
            return
        task = self.loop.create_task(coro)
        task.add_done_callback(self._taskFinished)
        self._background_tasks.append(task)
        return task

    def createWindow(self) -> Window:
        window = Window(self)
        window.setMainWindow(True) if not self._windows else ...
        self._windows.append(window)
        return window

    @property
    def mainWindow(self) -> Window:
        if not self._windows:
            window = Window(self)
            window.setMainWindow(True)
            self._windows.append(window)
        return self._windows[0]

    def closeWindow(self, window: Window):
        self._windows.remove(window)
        if window.isMainWindow():
            if not self._windows:
                return self.exit(0)
            self._windows[0].setMainWindow(True)

    def exec(self) -> None:
        if self.isRunning:
            return
        self.parseArgs(self.arguments())
        self.server.listen()
        self.loop.create_task(self.runEventLoop())
        self._isRunning = True
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.exit()

    def exit(self, code: int = 0) -> None:
        self._isClosing = True
        self._isRunning = False
        self.aboutToQuit.emit()
        for _ in range(len(self._windows)):
            self._windows[0].close()
        for task in self._background_tasks:
            task.cancel()
        return super().exit(code)

    def excepthook(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException | None,
        exc_tb: TracebackType,
    ):
        try:
            tbs, tb = [], exc_tb
            while tb is not None:
                tbs.append(
                    {
                        "file": Path(tb.tb_frame.f_code.co_filename),
                        "line": tb.tb_lineno,
                    }
                )
                tb = tb.tb_next
            end = False
            for tb in tbs[::-1]:
                file, line = tb["file"], tb["line"]
                if file.is_relative_to(self.localAppData):
                    break
                if end := file.is_relative_to(os.getcwd()):
                    break
            err = f"{file.name}({line}) - {exc_type.__name__}: {exc_value}"
            logging.error(err)
            if end:
                dialog = QMessageBox()
                dialog.setWindowTitle("Cipher")
                dialog.setText(f"Cipher has crashed.\n{err}")
                dialog.exec()
                return self.exit(0)
        except Exception:
            logging.error(f"{exc_type.__name__}: {exc_value}")
        traceback.print_exception(exc_type, exc_value, exc_tb)
