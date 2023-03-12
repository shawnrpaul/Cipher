from __future__ import annotations
from typing import Any, Dict, Iterable, Optional, TYPE_CHECKING, Union
from psutil import process_iter
from shutil import rmtree
from pathlib import Path
from copy import copy
import win32api, win32con
import win32clipboard
import json
import os

from .editor import Editor
from PyQt6.QtCore import pyqtSignal, QDir, QModelIndex, Qt, QDir
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QTreeView,
)


if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("FileManager",)


class FileSystemModel(QFileSystemModel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__currentFolder = None

    @property
    def currentFolder(self) -> Optional[Path]:
        return copy(self.__currentFolder)

    def setRootPath(self, path: Optional[Path]) -> QModelIndex:
        self.__currentFolder = path
        self.modelIndex = super().setRootPath(str(path) if path else None)
        return self.modelIndex


class FileManager(QTreeView):
    onWorkspaceChanged = pyqtSignal()
    onSave = pyqtSignal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("FileManager")
        self._window = window
        self.createContextMenu()
        self.__systemModel = FileSystemModel()
        settings = self.getSettings()
        if not settings.get("showHidden", False):
            self.setFilter(
                QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
            )
        else:
            self.setFilter(
                QDir.Filter.Hidden
                | QDir.Filter.NoDotAndDotDot
                | QDir.Filter.AllDirs
                | QDir.Filter.Files
            )

        self.__systemModel.setRootPath(settings.get("lastFolder"))

        self.setModel(self.__systemModel)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.menu.exec(self.viewport().mapToGlobal(pos))
        )

        self.clicked.connect(self.view)
        self.setIndentation(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setHeaderHidden(True)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    @property
    def currentFolder(self) -> Optional[Path]:
        return self.__systemModel.currentFolder

    def filePath(self, index: QModelIndex) -> str:
        return self.__systemModel.filePath(index)

    def setFilter(self, filters: QDir.Filter) -> None:
        return self.__systemModel.setFilter(filters)

    def saveFile(self) -> None:
        if not self._window.currentFile:
            return
        if not self._window.currentFile.path.exists():
            return self.saveAs()
        self._window.currentFile.path.write_text(self._window.currentFile.text())
        self.onSave.emit()
        if (
            str(self._window.currentFile.path.absolute())
            == f"{self._window.localAppData}\\settings.json"
        ):
            settings = self.getSettings()
            if not settings.get("showHidden", False):
                self.__systemModel.setFilter(
                    QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
                )
            else:
                self.__systemModel.setFilter(
                    QDir.Filter.Hidden
                    | QDir.Filter.NoDotAndDotDot
                    | QDir.Filter.AllDirs
                    | QDir.Filter.Files
                )

    def saveAs(self) -> None:
        if not self._window.currentFile:
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
            f.write(self._window.currentFile.text())
        self._window.currentFile.path = Path(file)
        self._window.currentFile.setText(
            self._window.currentFile.path.read_text(encoding="utf-8")
        )
        self._window.tabView.setTabText(
            self._window.tabView.currentIndex(), self._window.currentFile.path.name
        )
        self.onSave.emit()

    def createFile(self) -> None:
        if not self.currentFolder:
            index = self.selectedIndexes()
            if not index:
                return
            index = index[0]
        else:
            index = self.getIndex()
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        path = Path(f"{self.filePath(index)}\\{name}").absolute()
        counter = 0
        name = str(path).split(".")
        while path.exists():
            counter += 1
            path = Path(f"{name[0]} ({counter}).{'.'.join(name[1:])}").absolute()
        path.write_text("", "utf-8")
        editor = Editor(window=self._window, path=path)
        index = self._window.tabView.addTab(editor, path.name)
        self._window.tabView.setCurrentIndex(index)

    def createFolder(self) -> None:
        if not self.currentFolder:
            index = self.selectedIndexes()
            if not index:
                return
            index = index[0]
        else:
            index = self.getIndex()
        name, ok = QInputDialog.getText(
            self, "Folder Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if name and ok and name != index.data():
            self.__systemModel.mkdir(index, name)

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
        self._window.setEditorTab(path)

    def openFilePath(self) -> None:
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        path = Path(name).absolute()
        self._window.setEditorTab(path)

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

        self.changeFolder(folder)
        settings = self.getWorkspaceSettings()
        self._window.tabView.openTabs(settings["currentFile"], settings["openedFiles"])

    def closeFolder(self) -> None:
        currentFile = (
            self._window.currentFile.path if self._window.currentFile else None
        )
        files = copy(self._window.tabView.tabList)
        self._window.tabView.closeTabs()
        if not self.currentFolder:
            return
        self.saveWorkspaceFiles(currentFile, files)
        self.changeFolder(None)

    def rename(self) -> None:
        index = self.getIndex()
        name, ok = QInputDialog.getText(
            self, "Rename", "Rename", QLineEdit.EchoMode.Normal, index.data()
        )
        if not name or not ok or name == index.data():
            return
        path = Path(self.filePath(index)).absolute()
        newPath = path.rename(f"{path.parent}\\{name}").absolute()
        if newPath.is_file():
            for widget in self._window.tabView:
                if str(widget.path) == str(path):
                    self._window.tabView.setTabText(widget, name)
                    widget.path = newPath
                    break
            return

        for widget in self._window.tabView:
            if widget.path.is_relative_to(str(path)):
                widget.path = Path(
                    str(newPath) + str(widget.path).split(str(path))[1]
                ).absolute()

    def delete(self) -> None:
        index = self.getIndex()
        path = Path(self.filePath(index)).absolute()
        if not path.exists():
            return

        if path.is_file():
            for widget in self._window.tabView:
                if str(widget.path) == str(path):
                    self._window.tabView.removeTab(widget)
                    break
            try:
                return path.unlink()
            except PermissionError:
                return

        for widget in self._window.tabView:
            if widget.path.is_relative_to(str(path)):
                self._window.tabView.removeTab(widget)

        rmtree(path.absolute())

    def changeFolder(self, folder: Optional[str]) -> None:
        folder = Path(folder).absolute() if folder else None
        if folder and not folder.exists():
            folder = None
        self.setRootIndex(self.__systemModel.setRootPath(folder))
        self.onWorkspaceChanged.emit()

    def view(self, index: QModelIndex) -> None:
        path = Path(self.filePath(index))
        if not path.is_file():
            if not self.isExpanded(index):
                return self.expand(index)
            return self.collapse(index)

        return self._window.setEditorTab(path)

    def createContextMenu(self) -> None:
        self.menu = QMenu(self._window)
        self.menu.setObjectName("FileContextMenu")
        createFolder = self.menu.addAction("New Folder")
        createFolder.triggered.connect(self.createFolder)
        createFile = self.menu.addAction("New File")
        createFile.triggered.connect(self.createFile)
        self.menu.addSeparator()
        rename = self.menu.addAction("Rename")
        rename.triggered.connect(self.rename)
        delete = self.menu.addAction("Delete")
        delete.triggered.connect(self.delete)
        self.menu.addSeparator()
        copyPath = self.menu.addAction("Copy Path")
        copyPath.triggered.connect(self.copyPath)
        showInFolder = self.menu.addAction("Show in Folder")
        showInFolder.triggered.connect(self.showInFolder)
        hide = self.menu.addAction("Hide")
        hide.triggered.connect(self.hide)

    def copyPath(self) -> None:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(
            self.filePath(self.getIndex()), win32clipboard.CF_UNICODETEXT
        )
        win32clipboard.CloseClipboard()

    def showInFolder(self) -> None:
        path = self.filePath(self.getIndex())
        os.startfile(path)

    def hide(self) -> None:
        files = self.selectedIndexes()
        if not files:
            return
        file = files[0]
        self.setRowHidden(file.row(), file.parent(), True)

    def getIndex(self) -> QModelIndex:
        index = self.selectedIndexes()
        if not index or self.filePath(
            self.__systemModel.modelIndex
        ) not in self.filePath(index[0]):
            return self.__systemModel.modelIndex
        return index[0]

    def getSettings(self) -> Dict[str, Any]:
        with open(f"{self._window.localAppData}\\settings.json") as f:
            return json.load(f)

    def saveSettings(self) -> None:
        processes = tuple(process.name() for process in process_iter())
        if processes.count("Cipher.exe") > 1:
            return
        settings = self.getSettings()
        settings["lastFolder"] = str(self.currentFolder) if self.currentFolder else None
        if self.currentFolder:
            self.saveWorkspaceFiles(
                self._window.currentFile.path if self._window.currentFile else None,
                self._window.tabView.tabList,
            )
        with open(f"{self._window.localAppData}\\settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def saveWorkspaceFiles(self, currentFile: Path, files: Iterable[Editor]) -> None:
        settings = self.getWorkspaceSettings()
        settings["currentFile"] = str(currentFile) if currentFile else None
        settings["openedFiles"] = tuple(str(widget.path) for widget in files)
        with open(f"{self.currentFolder}\\.Cipher\\settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def getWorkspaceSettings(self) -> Dict[str, Union[str, Any]]:
        if not self.currentFolder:
            return {"project": None, "currentFile": None, "openedFiles": []}
        path = Path(f"{self.currentFolder}\\.Cipher").absolute()
        if not path.exists():
            path.mkdir()
            settings = self.getSettings()
            if settings.get("createHiddenCipherFolder"):
                win32api.SetFileAttributes(str(path), win32con.FILE_ATTRIBUTE_HIDDEN)
            with open(f"{path}\\terminal.json", "w") as f:
                json.dump({}, f, indent=4)

        path = Path(f"{path}\\settings.json").absolute()
        if not path.exists():
            with open(path, "w") as f:
                json.dump(
                    {"project": None, "currentFile": None, "openedFiles": []},
                    f,
                    indent=4,
                )

        with open(path) as f:
            return json.load(f)
