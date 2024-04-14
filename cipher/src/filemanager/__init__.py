from __future__ import annotations
from typing import Any, Iterator, TYPE_CHECKING
from pathlib import Path
import json
import os

from PyQt6.QtCore import pyqtSignal, QFileSystemWatcher
from PyQt6.QtWidgets import QFrame, QFileDialog, QInputDialog, QLineEdit, QVBoxLayout
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
        self._window = window
        self._treeViews: list[TreeView] = [TreeView(self)]
        self._splitter = TreeViewSplitter(self)

        self._globalSettings = QFileSystemWatcher([os.path.join(window.localAppData,"settings.cipher")], self)  # fmt:skip
        self._globalSettings.fileChanged.connect(self.updateSettings)
        self._workspaceSettings = QFileSystemWatcher(self)
        self._workspaceSettings.fileChanged.connect(self.updateSettings)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter)
        self.setLayout(layout)

    @property
    def window(self) -> Window:
        return self._window

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
    def settingsPath(self) -> Path | None:
        os.path.join
        if self.currentFolder:
            return Path(os.path.join(self.currentFolder, ".cipher", "settings.cipher"))
        return Path(os.path.join(self.window.localAppData, "settings.cipher"))

    def __iter__(self) -> Iterator[TreeView]:
        return iter(self._treeViews)

    def getPaths(self) -> tuple[Path]:
        return tuple(treeView.currentFolder for treeView in self._treeViews)

    def hasPath(self, path: Path) -> None:
        for treeView in self._treeViews:
            if treeView.currentFolder == path:
                return True
        return False

    def openFolder(self) -> None:
        """Changes the workspace"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Pick a Folder",
            str(self.currentFolder) if self.currentFolder else "C:/",
            options=QFileDialog().options(),
        )
        if not folder:
            return

        self.changeFolder(Path(folder))

    def openFolderTreeView(self) -> None:
        if not self.currentFolder:
            return
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a Folder", "C:/", options=QFileDialog().options()
        )
        if not folder:
            return
        self.addTreeView(Path(folder))

    def setSelectedIndex(self, widget: Tab) -> None:
        for treeView in self._treeViews:
            treeView.setSelectedIndex(widget)

    def getTreeView(self, path: Path) -> TreeView | None:
        for treeView in self._treeViews:
            if treeView.currentFolder == path:
                return treeView

    def addTreeView(self, path: Path | None) -> None:
        treeView = TreeView(self)
        treeView.setFolder(path)
        treeView.updateSettings()
        self._splitter.addWidget(treeView)
        self._treeViews.append(treeView)

    def removeTreeView(self, treeView: TreeView) -> None:
        self._treeViews.remove(treeView)
        treeView.deleteLater()

    def clearTreeViews(self) -> None:
        treeViews = self._treeViews[1:]
        for treeView in treeViews:
            self.removeTreeView

    def openFile(self, filePath: str | None = None) -> None:
        """Opens a file

        Parameters
        ----------
        filePath: :class:`~typing.Optional[str]`
            The file path of the file to open, by default None
        """
        if not filePath:
            options = QFileDialog().options()
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "Pick a file",
                str(self.currentFolder) if self.currentFolder else "C:/",
                "All Files (*);;C++ (*cpp *h *hpp);;JavaScript (*js);;JSON (*json);;Python (*py)",
                options=options,
            )

            if not filePath:
                return

        path = Path(filePath).absolute()
        if not path.is_file():
            return
        self.window.tabView.createTab(path)

    def openFilePath(self) -> None:
        """Opens a file with a given file path"""
        filePath, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not filePath or not ok:
            return
        self.openFile(filePath)

    def changeFolder(self, path: Path | None) -> None:
        if path == self.currentFolder:
            return
        window = self.window
        treeView = self.treeView
        if self.currentFolder:
            self.saveWorkspaceFiles()
        window.tabView.closeTabs()
        self.clearTreeViews()
        if self.currentFolder:
            self._workspaceSettings.removePath(
                os.path.join(self.currentFolder, ".cipher", "settings.cipher")
            )
        treeView.setFolder(path)
        self.updateSettings()
        self.openWorkspaceFiles()
        if path:
            self._workspaceSettings.addPath(
                os.path.join(path, ".cipher", "settings.cipher")
            )

    def closeFolder(self) -> None:
        self.saveWorkspaceFiles()
        self.window.tabView.closeTabs()
        self.treeView.setFolder(None)
        self.clearTreeViews()

    def updateSettings(self) -> None:
        window = self.window
        globalSettings = self.getGlobalSettings()
        workspaceSettings = self.getWorkspaceSettings()
        window.settings["showHidden"] = workspaceSettings.get(
            "showHidden", globalSettings.get("showHidden", False)
        )
        window.settings["hiddenPaths"] = list(
            {
                *globalSettings.get("hiddenPaths", []),
                *workspaceSettings.get("hiddenPaths", []),
            }
        )
        window.settings["search-pattern"] = workspaceSettings.get(
            "search-pattern", globalSettings.get("search-pattern", [])
        )
        window.settings["search-exclude"] = workspaceSettings.get(
            "search-exclude", globalSettings.get("search-exclude", [])
        )
        for treeview in self._treeViews:
            treeview.updateSettings()

    def createFile(self) -> None:
        return self.treeView.createFile()

    def createFolder(self) -> None:
        return self.treeView.createFolder()

    def getGlobalSettings(self) -> dict:
        with open(os.path.join(self.window.localAppData, "settings.cipher")) as f:
            return json.load(f)

    def getWorkspaceSettings(self) -> dict:
        if not self.currentFolder:
            return {}
        folder = Path(os.path.join(self.currentFolder, ".cipher"))
        if not folder.exists():
            folder.mkdir()
            if self.window.application.platformName() == "windows":
                with open(os.path.join(folder, "run.bat"), "w") as f:
                    f.write("@echo off\nEXIT")
            else:
                with open(os.path.join(folder, "run.sh"), "w") as f:
                    f.write("")
            with open(os.path.join(folder, "session.json"), "w") as f:
                json.dump({"currentFile": None, "openedFiles": []}, f, indent=4)
            data = {
                "showHidden": False,
                "hiddenPaths": [],
                "search-pattern": [],
                "search-exclude": [],
            }
            with open(os.path.join(folder, "settings.cipher"), "w") as f:
                json.dump(data, f, indent=4)
            return data
        with open(os.path.join(folder, "settings.cipher")) as f:
            return json.load(f)

    def openWorkspaceFiles(self) -> None:
        window = self.window
        path = os.path.join(self.currentFolder, ".cipher", "session.json")
        with open(path) as f:
            session = json.load(f)
        window.tabView.openTabs(session["currentFile"], session["openedFiles"])

    def saveWorkspaceFiles(self) -> None:
        window = self.window
        path = os.path.join(self.currentFolder, ".cipher", "session.json")
        with open(path) as f:
            session = json.load(f)
        session["currentFile"] = (
            str(window.currentFile.path) if window.currentFile else None
        )
        session["openedFiles"] = list(str(tab.path) for tab in window.tabView.tabList)
        with open(path, "w") as f:
            json.dump(session, f, indent=4)

    def resumeSession(self) -> None:
        with open(os.path.join(self.window.localAppData, "session.json")) as f:
            session = json.load(f)
        folder = Path(path) if (path := session.get("lastFolder")) else None
        if folder is None or not folder.exists():
            return
        self.changeFolder(folder)

    def saveSession(self) -> None:
        window = self.window
        if self.currentFolder:
            self.saveWorkspaceFiles()
        path = os.path.join(self.window.localAppData, "session.json")
        with open(path) as f:
            session = json.load(f)
        session["lastFolder"] = str(self.currentFolder) if self.currentFolder else None
        with open(path, "w") as f:
            json.dump(session, f, indent=4)
