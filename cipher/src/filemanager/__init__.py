from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pathlib import Path
from copy import copy

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout
from ..tabview import Tab
from .treeview import *
from .splitter import *

if TYPE_CHECKING:
    from cipher import Window

__all__ = ("FileManager",)


class FileManager(QFrame):
    workspaceChanged = pyqtSignal(object)
    folderCreated = pyqtSignal(Path)
    fileCreated = pyqtSignal(Path)
    fileSaved = pyqtSignal(Tab)

    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._treeViews: list[TreeView] = [MainTreeView(window)]
        self._splitter = TreeViewSplitter(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter)
        self.setLayout(layout)

    @property
    def window(self) -> Window:
        return super().window()

    @property
    def treeView(self) -> TreeView:
        return self._treeViews[0]

    @property
    def splitter(self) -> None:
        return self._splitter

    @property
    def currentFolder(self) -> Path | None:
        return self.treeView.currentFolder

    @property
    def settingsPath(self) -> Path:
        return self.treeView.settingsPath

    def getCurrentSettings(self) -> dict[str, Any]:
        return self.treeView.getCurrentSettings()

    def getGlobalSettings(self) -> dict[str, Any]:
        return self.treeView.getGlobalSettings()

    def getWorkspaceSettings(self) -> dict[str, Any]:
        return self.treeView.getWorkspaceSettings()

    def saveSettings(self) -> None:
        return self.treeView.saveSettings()

    def getPaths(self) -> list[Path]:
        return [treeView.currentFolder for treeView in self._treeViews[1:]]

    def hasPath(self, path: Path) -> None:
        for treeView in self._treeViews:
            if treeView.currentFolder == path:
                return True
        return False

    def changeFolder(self, path: Path | None) -> None:
        if path == self.currentFolder:
            return
        window = self.window
        treeView = self.treeView
        if self.currentFolder:
            currentFile = window.currentFile.path if window.currentFile else None
            treeView.saveWorkspaceFiles(currentFile, copy(window.tabView.tabList))
        self.clear()
        window.tabView.closeTabs()
        treeView.setFolder(path)

    def setSelectedIndex(self, widget: Tab) -> None:
        for treeView in self._treeViews:
            treeView.setSelectedIndex(widget)

    def getTreeView(self, path: Path) -> TreeView | None:
        for treeView in self._treeViews:
            if treeView.currentFolder == path:
                return treeView

    def addTreeView(self, path: Path | None) -> None:
        treeView = TreeView(self.window)
        treeView.changeFolder(path)
        treeView.workspaceChanged.connect(self.workspaceChanged.emit)
        treeView.folderCreated.connect(self.folderCreated.emit)
        treeView.fileCreated.connect(self.fileCreated.emit)
        treeView.fileSaved.connect(self.fileSaved.emit)
        self._splitter.addWidget(treeView)
        self._treeViews.append(treeView)

    def removeTreeView(self, path: Path) -> None:
        if not (treeView := self.getTreeView(path)):
            return
        treeView.deleteLater()

    def clear(self) -> None:
        for treeView in self._treeViews[1:]:
            treeView.deleteLater()
