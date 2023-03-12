from __future__ import annotations
from typing import Any, Callable, Optional, Type, TYPE_CHECKING
from pathlib import Path
from functools import wraps
from types import TracebackType
from importlib import import_module
import logging
import asyncio
import json
import traceback
import sys
import os

from .body import *
from .extensionlist import *
from .filemanager import *
from .menubar import *
from .sidebar import *
from .tab import *
from .thread import *
from ext.extension import Extension
from ext.exceptions import EventTypeError

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtGui import QDropEvent, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter

if TYPE_CHECKING:
    from .editor import Editor

__all__ = ("run",)

localAppData = os.path.join(os.getenv("LocalAppData"), "Cipher")
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s: %(message)s")
fileHandler = logging.FileHandler(f"{localAppData}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self._threadPool = QThreadPool.globalInstance()
        self.localAppData = localAppData
        self.setWindowIcon(QIcon(f"{localAppData}\\icons\\window.png"))

        self.body = Body(self)
        self.tabView = TabWidget(self)
        self.fileManager = FileManager(self)
        self.extensions = ExtensionList(self)
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)

        self.setMenuBar(self.menubar)
        self.body._layout.addWidget(self.sidebar)
        self.hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.hsplit.addWidget(self.sidebar.explorer)
        self.hsplit.addWidget(self.tabView)
        self.body._layout.addWidget(self.hsplit)
        self.body.setLayout()
        self.setCentralWidget(self.body)

        self.setStyleSheet(open(f"{localAppData}\\styles\\styles.qss").read())

        sys.path.insert(0, f"{localAppData}\\include")
        sys.path.insert(0, f"{localAppData}\\site-packages")

        self.tabView.setupTabs()
        self.tabView.currentChanged.connect(self.currentChanged)

        self._events = {}
        self._events["widgetChanged"] = []
        self._events["onWorkspaceChanged"] = []
        self._events["onSave"] = []
        self._events["onClose"] = []
        self.fileManager.onWorkspaceChanged.connect(self.onWorkspaceChanged)
        self.fileManager.onSave.connect(self.onSave)

        self._loop = asyncio.get_event_loop()
        self._thread = Thread(self.addExtensions)
        self._thread.start()
        self.showMaximized()

    @property
    def currentFolder(self) -> Path:
        return self.fileManager.currentFolder

    @property
    def currentFile(self) -> Editor:
        return self.tabView.currentFile

    def addExtensions(self) -> None:
        extensions = f"{localAppData}\\include\\extension"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}\\{folder}").absolute()
            settings = Path(f"{path}\\settings.json").absolute()
            self._threadPool.start(Runnable(self.addExtension, path, settings))

    def addExtension(self, path: Path, settings: Path) -> None:
        if not path.exists() or not settings.exists():
            return
        with open(settings) as f:
            data = json.load(f)

        name = data.get("name")
        if not name:
            return

        if data.get("enabled"):
            try:
                mod = import_module(f"extension.{path.name}.run")
                obj = mod.run(loop=self._loop)
            except EventTypeError:
                pass
            except Exception as e:
                logger.error(f"Failed to add Extension - {e.__class__.__name__}: {e}")
                return
            if not isinstance(obj, Extension):
                return
            obj._inject()
            self._events["widgetChanged"].extend(
                obj.__events__.get("widgetChanged", [])
            )
            self._events["onWorkspaceChanged"].extend(
                obj.__events__.get("onWorkspaceChanged", [])
            )
            self._events["onSave"].extend(obj.__events__.get("onSave", []))
            self._events["onClose"].extend(obj.__events__.get("onClose", []))
            onReady = obj.__events__.get("onReady", ())
        else:
            name = f"{name} (Disabled)"
        self.extensions.addItem(ExtensionItem(name, f"{path}\\icon.ico", settings))
        for func in onReady:
            self._threadPool.start(Runnable(func, self.currentFolder, self.currentFile))

    def currentChanged(self, _: int) -> None:
        for func in self._events.get("widgetChanged", []):
            self._threadPool.start(Runnable(func, self.currentFolder, self.currentFile))

    def onWorkspaceChanged(self) -> None:
        for func in self._events.get("onWorkspaceChanged", []):
            self._threadPool.start(Runnable(func, self.currentFolder))

    def onSave(self) -> None:
        for func in self._events.get("onSave", []):
            self._threadPool.start(Runnable(func, self.currentFile))

    def close(self) -> None:
        for func in self._events.get("onClose", []):
            self._threadPool.start(Runnable(func))

    def fileDropped(self, a0: QDropEvent) -> bool:
        urls = a0.mimeData().urls()
        if not urls:
            return
        path = urls[0]
        if path.isLocalFile():
            self.setEditorTab(Path(path.toLocalFile()))
            return True
        return False

    def saveFile(self) -> None:
        self.fileManager.saveFile()

    def saveAs(self) -> None:
        self.fileManager.saveAs()

    def createFile(self) -> None:
        self.fileManager.createFile()

    def createFolder(self) -> None:
        self.fileManager.createFolder()

    def openFile(self) -> None:
        self.fileManager.openFile()

    def openFilePath(self) -> None:
        self.fileManager.openFilePath()

    def openFolder(self) -> None:
        self.fileManager.openFolder()

    def closeFolder(self) -> None:
        self.fileManager.closeFolder()

    def find(self) -> None:
        self.currentFile.find() if self.currentFile else ...

    def copy(self) -> None:
        self.currentFile.copy() if self.currentFile else ...

    def cut(self) -> None:
        self.currentFile.cut() if self.currentFile else ...

    def paste(self) -> None:
        self.currentFile.paste() if self.currentFile else ...

    def rename(self) -> None:
        self.fileManager.rename()

    def delete(self) -> None:
        self.fileManager.delete()

    def setEditorTab(self, path: Path) -> Editor:
        return self.tabView.setEditorTab(path)


def excepthook(
    func: Callable[[Type[BaseException], Optional[BaseException], TracebackType], Any],
    app: QApplication,
) -> Any:

    wraps(func)

    def log(
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_tb: TracebackType,
    ) -> Any:
        tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
        frame = tb.stack[-1]
        file = Path(frame.filename).name
        line = frame.lineno
        logger.error(f"{file}({line}) - {exc_type.__name__}: {exc_value}")
        app.quit()
        return func(exc_type, exc_value, exc_tb)

    return log


def run() -> None:
    app = QApplication([])
    sys.excepthook = excepthook(sys.excepthook, app)
    window = MainWindow()
    app.aboutToQuit.connect(window.close)
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()
