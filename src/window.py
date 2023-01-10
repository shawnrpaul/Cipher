from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, Tuple
import logging
import asyncio
import json
import sys
import os

from .body import Body
from .editor import *
from .explorer import *
from .extensions import *
from .filemanager import *
from .folder import *
from .menubar import *
from .sidebar import *
from .tab import *
from .thread import *

from PyQt6.QtCore import QDir, Qt, QThreadPool
from PyQt6.QtGui import QIcon
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
format = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
fileHandler = logging.FileHandler(
    f"{os.path.dirname(os.path.dirname(__file__))}\\logs.log"
)
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self.localAppData = os.path.join(os.getenv("LocalAppData"), "Cipher")
        settings = self.getSettings()
        icons = f"{self.localAppData}\\icons"
        self.currentFile = None
        self.setWindowIcon(QIcon(f"{icons}\\window.png"))
        self.styles = settings.get("styles")
        if not self.styles or not Path(self.styles).absolute().exists():
            self.styles = f"{self.localAppData}\\styles"
        self.currentFolder = Folder(settings.get("lastFolder"))
        currentFile = settings.get("lastFile")

        self.menubar = Menubar(self)
        self.body = Body()
        self.tabView = TabWidget()
        self.fileManager = FileManager(self, settings.get("showHidden", False))
        self.explorer = Explorer(self)
        self.extensions = ExtensionList(self)
        self.sidebar = Sidebar(self)

        self.setMenuBar(self.menubar)
        self.body._layout.addWidget(self.sidebar)
        self.hsplit = QSplitter(Qt.Orientation.Horizontal)
        self.hsplit.addWidget(self.explorer)
        self.hsplit.addWidget(self.tabView)
        self.body._layout.addWidget(self.hsplit)
        self.body.setLayout()

        self.setCentralWidget(self.body)
        self.statusbar = self.statusBar()

        self.setStyleSheet(open(f"{self.styles}\\styles.qss").read())

        for path in settings.get("lastFilesList", ()):
            path = Path(path)
            if path.exists():
                self.setEditorTab(path)
                if currentFile == str(path):
                    self.currentFile = self.tabView.currentWidget()

        if self.currentFile:
            self.tabView.setCurrentWidget(self.currentFile)

        self._loop = asyncio.get_event_loop()
        self._thread = Thread(self.addExtensions)
        self._thread.start()
        self.showMaximized()

    def ready(self) -> None:
        self.currentFile = self.tabView.currentWidget()
        for func in self._events["onReady"]:
            self._threadPool.start(Runnable(func, self.currentFile))

    def currentChanged(self, _: int):
        self.currentFile = self.tabView.currentWidget()
        for func in self._events["widgetChanged"]:
            self._threadPool.start(Runnable(func, self.currentFile))

    def close(self) -> None:
        for func in self._events["onClose"]:
            self._threadPool.start(Runnable(func))

    def addExtensions(self) -> None:
        sys.path.insert(0, f"{self.localAppData}\\extensions")
        from ext.extension import Extension
        from importlib import import_module

        self._events = {}
        self._events["onReady"] = []
        self._events["widgetChanged"] = []
        self._events["onClose"] = []
        items = []

        self._threadPool = QThreadPool.globalInstance()
        extensions = f"{self.localAppData}\\extensions\\extensions"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}\\{folder}").absolute()
            settings = Path(f"{path}\\settings.json").absolute()
            if not path.exists() or not settings.exists():
                continue
            mod = import_module(f"extensions.{path.name}.run")
            try:
                obj = mod.run(
                    currentFolder=self.currentFolder,
                    explorer=self.explorer,
                    menubar=self.menubar,
                    statusbar=self.statusbar,
                    loop=self._loop,
                )
            except Exception as e:
                logger.error(f"Failed to add Extension - {e.__class__}: {e}")
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
        self.tabView.currentChanged.connect(self.currentChanged)
        for extension in items:
            self.extensions.addItem(extension)
        self.ready()

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
            return
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
        editor = Editor(path, styles=self.styles)
        index = self.tabView.addTab(editor, path.name)
        self.tabView.setCurrentIndex(index)

    def createFolder(self) -> None:
        if not self.currentFolder:
            return
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

        self.currentFolder.changeFolder(folder)
        self.fileManager.systemModel.setRootPath(folder)
        self.fileManager.setRootIndex(self.fileManager.systemModel.index(folder))

    def closeFolder(self) -> None:
        self.currentFolder.changeFolder(None)
        self.fileManager.systemModel.setRootPath(None)
        self.fileManager.setRootIndex(self.fileManager.systemModel.index(None))
        count = self.tabView.count()
        for _ in range(count):
            self.tabView.removeTab(0)

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
            for tab in range(self.tabView.count()):
                widget = self.tabView.widget(tab)
                if str(widget.path) == str(path):
                    self.tabView.setTabText(tab, name)
                    widget.path = newPath
                    break
            return

        for tab in range(self.tabView.count()):
            widget = self.tabView.widget(tab)
            if widget.path.is_relative_to(str(path)):
                widget.path = Path(
                    str(newPath) + str(widget.path).split(str(path))[1]
                ).absolute()
                break

    def delete(self) -> None:
        index = self.fileManager.getIndex()
        path = Path(self.fileManager.systemModel.filePath(index)).absolute()
        if not path.exists():
            return

        if path.is_file():
            for tab in range(self.tabView.count()):
                widget = self.tabView.widget(tab)
                if str(widget.path) == str(path):
                    self.tabView.removeTab(tab)
                    break
            return path.unlink()

        rmtree(path.absolute())
        for tab in range(self.tabView.count()):
            widget = self.tabView.widget(tab)
            if widget.path.is_relative_to(str(path)):
                self.tabView.removeTab(tab)
                break

    def isBinary(self, path) -> None:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def setEditorTab(self, path: Path) -> None:
        if not path.exists():
            return
        if not path.is_file():
            return
        if self.isBinary(path):
            return

        if str(path.absolute()) in tuple(
            str(self.tabView.widget(i).path.absolute())
            for i in range(self.tabView.count())
        ):
            return

        editor = Editor(path=path, styles=self.styles)
        editor.setText(path.read_text(encoding="utf-8"))
        self.tabView.addTab(editor, path.name)
        self.tabView.setCurrentWidget(editor)

    def getSettings(self) -> Dict[str, Any]:
        with open(f"{self.localAppData}\\settings.json") as f:
            return json.load(f)

    def changeLast(
        self, folder: Folder = None, file: Path = None, tabs: Tuple[str] = None
    ) -> None:
        settings = self.getSettings()
        if folder:
            settings["lastFolder"] = str(folder)
        else:
            settings["lastFolder"] = None
        if file:
            settings["lastFile"] = str(file.absolute())
        else:
            settings["lastFile"] = None
        settings["lastFilesList"] = tabs
        with open(f"{self.localAppData}\\settings.json", "w") as f:
            json.dump(settings, f, indent=4)


def run() -> None:
    app = QApplication([])
    window = MainWindow()
    app.aboutToQuit.connect(
        lambda: window.changeLast(
            folder=window.currentFolder,
            file=window.currentFile.path if window.currentFile else None,
            tabs=tuple(
                str(window.tabView.widget(i).path.absolute())
                for i in range(window.tabView.count())
            ),
        )
    )
    app.aboutToQuit.connect(window.close)
    app.exec()
