from copy import copy
from pathlib import Path
from psutil import process_iter
from shutil import rmtree
from functools import wraps
from types import TracebackType
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Type
import logging
import asyncio
import json
import traceback
import sys
import os

from .body import Body
from .editor import *
from .explorer import *
from .extensionlist import *
from .filemanager import *
from .folder import *
from .menubar import *
from .sidebar import *
from .tab import *
from .terminal import *
from .thread import *
from ext.extension import Extension
from ext.exceptions import EventTypeError

from PyQt6.QtCore import QDir, Qt, QThreadPool
from PyQt6.QtGui import QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QSplitter,
)

__all__ = ("run",)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s: %(message)s")
fileHandler = logging.FileHandler(
    f"{os.path.dirname(os.path.dirname(__file__))}\\logs.log"
)
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self._threadPool = QThreadPool.globalInstance()
        self.localAppData = os.path.join(os.getenv("LocalAppData"), "Cipher")
        settings = self.getSettings()
        self.setWindowIcon(QIcon(f"{self.localAppData}\\icons\\window.png"))
        self.currentFolder = Folder(None)
        self.currentFile = None

        self.body = Body(self)
        self.tabView = TabWidget(self)
        self.fileManager = FileManager(self, settings.get("showHidden", False))
        self.explorer = Explorer(self)
        self.extensions = ExtensionList(self)
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)

        self.setMenuBar(self.menubar)
        self.body._layout.addWidget(self.sidebar)
        self.hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.hsplit.addWidget(self.explorer)
        self.hsplit.addWidget(self.tabView)
        self.body._layout.addWidget(self.hsplit)
        self.body.setLayout()
        self.setCentralWidget(self.body)
        self.statusbar = self.statusBar()

        self.setStyleSheet(open(f"{self.localAppData}\\styles\\styles.qss").read())

        self.setupTabs()
        self.tabView.currentChanged.connect(self.currentChanged)

        self._loop = asyncio.get_event_loop()
        self._thread = Thread(self.addExtensions)
        self._thread.start()
        self.showMaximized()

    def setupTabs(self):
        if len(sys.argv) > 1:
            self.fileManager.changeFolder(None)
            self.currentFile = self.setEditorTab(Path(sys.argv[1]))
            return

        settings = self.getSettings()
        folder = settings.get("lastFolder")
        if folder and not Path(folder).absolute().exists():
            folder = None
        self.fileManager.changeFolder(folder)
        if self.currentFolder:
            settings = self.fileManager.getWorkspaceSettings()
            self.openTabs(settings.get("currentFile"), settings.get("openedFiles"))

    def openTabs(self, currentFile: str, files: List[str]):
        currentWidget = None
        for path in files:
            window = self.setEditorTab(Path(path))
            if currentFile == path:
                currentWidget = window

        if currentWidget:
            self.tabView.setCurrentWidget(currentWidget)
            self.currentFile = currentWidget

    def ready(self) -> None:
        self.currentFile = self.tabView.currentWidget()
        for func in self._events["onReady"]:
            self._threadPool.start(Runnable(func, self.currentFile))

    def currentChanged(self, _: int):
        self.currentFile = self.tabView.currentWidget()
        for func in self._events["widgetChanged"]:
            self._threadPool.start(Runnable(func, self.currentFile))

    def close(self) -> None:
        self.currentFile = self.tabView.currentWidget()
        for func in self._events["onClose"]:
            self._threadPool.start(Runnable(func))

    def addExtensions(self) -> None:
        sys.path.insert(0, f"{self.localAppData}\\include")

        self._events = {}
        self._events["onReady"] = []
        self._events["widgetChanged"] = []
        self._events["onClose"] = []
        items = []

        extensions = f"{self.localAppData}\\include\\extension"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}\\{folder}").absolute()
            settings = Path(f"{path}\\settings.json").absolute()
            if not path.exists() or not settings.exists():
                continue
            with open(settings) as f:
                data = json.load(f)
                if not data.get("enabled"):
                    continue
            try:
                mod = import_module(f"extension.{path.name}.run")
                obj = mod.run(
                    currentFolder=self.currentFolder,
                    explorer=self.explorer,
                    menubar=self.menubar,
                    statusbar=self.statusbar,
                    loop=self._loop,
                )
            except EventTypeError:
                pass
            except Exception as e:
                print(e.__class__, e)
                logger.error(f"Failed to add Extension - {e.__class__.__name__}: {e}")
                continue
            if not isinstance(obj, Extension):
                continue
            obj._inject()
            self._events["onReady"].extend(obj.__events__.get("onReady", []))
            self._events["widgetChanged"].extend(
                obj.__events__.get("widgetChanged", [])
            )
            self._events["onClose"].extend(obj.__events__.get("onClose", []))
            try:
                items.append(ExtensionItem(obj.__name__, f"{path}\\icon.ico", settings))
            except Exception:
                items.append(
                    ExtensionItem(obj.__class__.__name__, f"{path}\\icon.ico", settings)
                )
        for extension in items:
            self.extensions.addItem(extension)
        self.ready()

    def fileDropped(self, a0: QDropEvent) -> bool:
        path = a0.mimeData().urls()[0]
        if path.isLocalFile():
            self.setEditorTab(Path(path.toLocalFile()))
            return True
        return False

    def saveFile(self) -> None:
        editor = self.currentFile
        if not editor:
            return
        if not editor.path.exists():
            return self.saveAs()
        editor.path.write_text(editor.text())
        if str(editor.path.absolute()) == f"{self.localAppData}\\settings.json":
            settings = self.getSettings()
            if not settings.get("showHidden", False):
                self.fileManager.systemModel.setFilter(
                    QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
                )
            else:
                self.fileManager.systemModel.setFilter(
                    QDir.Filter.Hidden
                    | QDir.Filter.NoDotAndDotDot
                    | QDir.Filter.AllDirs
                    | QDir.Filter.Files
                )

    def saveAs(self) -> None:
        editor = self.currentFile
        if not editor:
            return
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            str(self.currentFolder) if self.currentFolder else "C:\\",
            "All Files (*);;Python files (*.py);;JSON files (*.json)",
        )
        if not file:
            return
        with open(f"{file}", "w") as f:
            f.write(editor.text())
        editor.path = Path(file)
        editor.setText(editor.path.read_text(encoding="utf-8"))
        self.tabView.setTabText(self.tabView.currentIndex(), editor.path.name)

    def createFile(self) -> None:
        if not self.currentFolder:
            index = self.fileManager.selectedIndexes()
            if not index:
                return
            index = index[0]
        else:
            index = self.fileManager.getIndex()
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        path = Path(
            f"{self.fileManager.systemModel.filePath(index)}\\{name}"
        ).absolute()
        counter = 0
        name = str(path).split(".")
        while path.exists():
            counter += 1
            path = Path(f"{name[0]} ({counter}).{'.'.join(name[1:])}").absolute()
        path.write_text("", "utf-8")
        editor = Editor(window=self, path=path)
        index = self.tabView.addTab(editor, path.name)
        self.tabView.setCurrentIndex(index)

    def createFolder(self) -> None:
        if not self.currentFolder:
            index = self.fileManager.selectedIndexes()
            if not index:
                return
            index = index[0]
        else:
            index = self.fileManager.getIndex()
        name, ok = QInputDialog.getText(
            self, "Folder Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if name and ok and name != index.data():
            self.fileManager.systemModel.mkdir(index, name)

    def openFile(self) -> None:
        options = QFileDialog().options()
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Pick a file",
            str(self.currentFolder) if self.currentFolder else "C:\\",
            "All Files (*);;Python files (*py);;JSON files (*.json)",
            options=options,
        )

        if not file:
            return

        path = Path(file).absolute()
        if not path.is_file():
            return
        self.setEditorTab(path)

    def openFilePath(self) -> None:
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        path = Path(name).absolute()
        self.setEditorTab(path)

    def openFolder(self) -> None:
        options = QFileDialog().options()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Pick a Folder",
            str(self.currentFolder) if self.currentFolder else "C:\\",
            options=options,
        )
        if not folder:
            return

        self.fileManager.changeFolder(folder)
        settings = self.fileManager.getWorkspaceSettings()
        self.openTabs(settings["currentFile"], settings["openedFiles"])

    def closeFolder(self) -> None:
        currentFile = self.currentFile.path if self.currentFile else None
        files = copy(self.tabView.tabList)
        self.tabView.closeTabs()
        if not self.currentFolder:
            return
        self.fileManager.saveWorkspaceFiles(currentFile, files)
        self.fileManager.changeFolder(None)

    def find(self):
        self.currentFile.find() if self.currentFile else ...

    def copy(self) -> None:
        self.currentFile.copy() if self.currentFile else ...

    def cut(self) -> None:
        self.currentFile.cut() if self.currentFile else ...

    def paste(self) -> None:
        self.currentFile.paste() if self.currentFile else ...

    def rename(self) -> None:
        index = self.fileManager.getIndex()
        name, ok = QInputDialog.getText(
            self, "Rename", "Rename", QLineEdit.EchoMode.Normal, index.data()
        )
        if not name or not ok or name == index.data():
            return
        path = Path(self.fileManager.systemModel.filePath(index)).absolute()
        newPath = path.rename(name).absolute()
        if newPath.is_file():
            for widget in self.tabView:
                if str(widget.path) == str(path):
                    self.tabView.setTabText(widget, name)
                    widget.path = newPath
                    break
            return

        for widget in self.tabView:
            if widget.path.is_relative_to(str(path)):
                widget.path = Path(
                    str(newPath) + str(widget.path).split(str(path))[1]
                ).absolute()

    def delete(self) -> None:
        index = self.fileManager.getIndex()
        path = Path(self.fileManager.systemModel.filePath(index)).absolute()
        if not path.exists():
            return

        if path.is_file():
            for widget in self.tabView:
                if str(widget.path) == str(path):
                    self.tabView.removeTab(widget)
                    break

            return path.unlink()

        for widget in self.tabView:
            if widget.path.is_relative_to(str(path)):
                self.tabView.removeTab(widget)

        rmtree(path.absolute())

    def isBinary(self, path) -> None:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def setEditorTab(self, path: Path) -> Editor:
        path = path.absolute()
        if not path.exists():
            return
        if not path.is_file():
            return
        if self.isBinary(path):
            return

        for widget in self.tabView:
            if path == widget.path:
                return

        editor = Editor(window=self, path=path)
        editor.setText(path.read_text(encoding="utf-8"))
        self.tabView.addTab(editor, path.name)
        self.tabView.setCurrentWidget(editor)

        return editor

    def getSettings(self) -> Dict[str, Any]:
        with open(f"{self.localAppData}\\settings.json") as f:
            return json.load(f)

    def saveSettings(self) -> None:
        processes = tuple(process.name() for process in process_iter())
        if processes.count("Cipher.exe") > 1:
            return
        settings = self.getSettings()
        settings["lastFolder"] = str(self.currentFolder) if self.currentFolder else None
        if self.currentFolder:
            self.fileManager.saveWorkspaceFiles(
                self.currentFile.path if self.currentFile else None,
                self.tabView.tabList,
            )
        with open(f"{self.localAppData}\\settings.json", "w") as f:
            json.dump(settings, f, indent=4)


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
        tb = (
            traceback.format_exception(exc_type, exc_value, exc_tb)[-2]
            .split("\n")[0]
            .split(",")
        )
        file = tb[0].split("\\")[-1].strip('"')
        logger.error(
            f"{file}({tb[1][1:]}) - {exc_value.__class__.__name__}: {exc_value}"
        )
        app.quit()
        return func(exc_type, exc_value, exc_tb)

    return log


def run() -> None:
    app = QApplication([])
    sys.excepthook = excepthook(sys.excepthook, app)
    window = MainWindow()
    app.aboutToQuit.connect(window.saveSettings)
    app.aboutToQuit.connect(window.close)
    app.exec()
