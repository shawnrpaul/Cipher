from __future__ import annotations
from PyQt6.QtCore import QDir, QModelIndex, Qt
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QMenu, QSizePolicy, QTreeView
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .window import MainWindow

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
        currentDir = str(window.currentFolder) if window.currentFolder else None
        self.styles = window.styles
        self.setEditorTab = window.setEditorTab
        self.createContextMenu(window)
        self.systemModel = FileSystem()
        self.systemModel.setRootPath(currentDir)
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
        self.setRootIndex(self.systemModel.index(currentDir))
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
            index = self.systemModel.modelIndex
        else:
            index = index[0]

        return index

    def view(self, index: QModelIndex) -> None:
        path = Path(self.systemModel.filePath(index))
        if not path.is_file():
            if not self.isExpanded(index):
                return self.expand(index)
            return self.collapse(index)

        return self.setEditorTab(path)
