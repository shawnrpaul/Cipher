from __future__ import annotations
from PyQt6.QtCore import QDir, QModelIndex, Qt
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QMenu, QSizePolicy, QTreeView
from typing import Any, Dict, Iterable, Optional, TYPE_CHECKING, Union
from pathlib import Path
import ctypes
import json

if TYPE_CHECKING:
    from .window import MainWindow
    from .editor import Editor

__all__ = ("FileManager",)


class FileSystem(QFileSystemModel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.modelIndex = None

    def setRootPath(self, path: str) -> QModelIndex:
        self.modelIndex = super().setRootPath(path)
        return self.modelIndex


class FileManager(QTreeView):
    def __init__(self, window: MainWindow, showHidden: bool) -> None:
        super().__init__()
        self.setObjectName("FileManager")
        self.currentFolder = window.currentFolder
        self.setEditorTab = window.setEditorTab
        self.createContextMenu(window)
        self.systemModel = FileSystem()
        if not showHidden:
            self.systemModel.setFilter(
                QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
            )
        else:
            self.systemModel.setFilter(
                QDir.Filter.Hidden
                | QDir.Filter.NoDotAndDotDot
                | QDir.Filter.AllDirs
                | QDir.Filter.Files
            )

        self.setModel(self.systemModel)
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

    def changeFolder(self, folder: Optional[str]):
        self.currentFolder.changeFolder(folder)
        self.setRootIndex(self.systemModel.setRootPath(folder))

    def createContextMenu(self, window: MainWindow) -> None:
        self.menu = QMenu(window)
        self.menu.setObjectName("FileContextMenu")
        createFolder = self.menu.addAction("New Folder")
        createFolder.triggered.connect(window.createFolder)
        createFile = self.menu.addAction("New File")
        createFile.triggered.connect(window.createFile)
        self.menu.addSeparator()
        rename = self.menu.addAction("Rename")
        rename.triggered.connect(window.rename)
        delete = self.menu.addAction("Delete")
        delete.triggered.connect(window.delete)

    def getIndex(self) -> QModelIndex:
        index = self.selectedIndexes()
        if not index or self.systemModel.filePath(
            self.systemModel.modelIndex
        ) not in self.systemModel.filePath(index[0]):
            return self.systemModel.modelIndex
        return index[0]

    def view(self, index: QModelIndex) -> None:
        path = Path(self.systemModel.filePath(index))
        if not path.is_file():
            if not self.isExpanded(index):
                return self.expand(index)
            return self.collapse(index)

        return self.setEditorTab(path)

    def saveWorkspaceFiles(self, currentFile: Path, files: Iterable[Editor]) -> None:
        settings = self.getWorkspaceSettings()
        settings["currentFile"] = str(currentFile) if currentFile else None
        settings["openedFiles"] = tuple(str(widget.path) for widget in files)
        with open(f"{self.currentFolder}\\.Cipher\\settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def getWorkspaceSettings(self) -> Dict[str, Union[str, Any]]:
        if not self.currentFolder:
            return {"venv": None, "currentFile": None, "openedFiles": []}
        path = Path(f"{self.currentFolder}\\.Cipher").absolute()
        if not path.exists():
            path.mkdir()
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x02)

        path = Path(f"{path}\\settings.json").absolute()
        if not path.exists():
            with open(path, "w") as f:
                json.dump(
                    {"venv": None, "currentFile": None, "openedFiles": []}, f, indent=4
                )

        with open(path) as f:
            return json.load(f)
