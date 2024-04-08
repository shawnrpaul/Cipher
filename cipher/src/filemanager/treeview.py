from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterable, Union
from pathlib import Path
import json
import subprocess
import sys

from PyQt6.QtCore import QDir, QFileSystemWatcher, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTreeView,
)

from .model import FileSystemModel
from ..tabview import Tab, Editor

if TYPE_CHECKING:
    from ..window import Window

__all__ = ("TreeView", "MainTreeView")


class TreeView(QTreeView):
    """The tree view of files and folders

    Parameters
    ----------
    window: :class:`Window`
        The code editor window

    Attributes
    ----------
    workspaceChanged: :class:`pyqtSignal`
        A signal emitted when the workspace is changed
    folderCreated: :class:`pyqtSignal`
        A signal emitted when the folder is created
    fileCreated: :class:`pyqtSignal`
        A signal emitted when the file is created
    fileSaved: :class:`pyqtSignal`
        A signal emitted when a file is saved
    """

    workspaceChanged = pyqtSignal(object)
    folderCreated = pyqtSignal(Path)
    fileCreated = pyqtSignal(Path)
    fileSaved = pyqtSignal(Tab)

    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.setObjectName("FileManager")
        self.createContextMenu()
        self._systemModel = FileSystemModel(self)

        self.setModel(self._systemModel)
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
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)

        self._globalSettings = QFileSystemWatcher(
            [f"{window.localAppData}/settings.json"], self
        )
        self._globalSettings.fileChanged.connect(lambda: self.updateSettings())
        self._workspaceSettings = QFileSystemWatcher(self)
        self._workspaceSettings.fileChanged.connect(lambda: self.updateSettings())

    @property
    def window(self) -> Window:
        return super().window()

    @property
    def currentFolder(self) -> Path | None:
        """Returns the :class:`~pathlib.Path` if there is a workspace.

        Returns
        -------
        :class:`~typing.Optional[~pathlib.Path]`
            The path of the workspace
        """
        return self._systemModel.currentFolder

    @property
    def settingsPath(self) -> Path:
        """Returns the current settings.

        Returns
        -------
        :class:`Path`
            The path of global or workspace settings
        """
        return self._systemModel.settingsPath

    def mousePressEvent(self, e: QMouseEvent):
        self.setFocus()
        if not self.indexAt(e.pos()).data():
            self.clearSelection()
        return super().mousePressEvent(e)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == int(Qt.Key.Key_Delete):
            self.delete()
            return event.accept()
        elif key == int(Qt.Key.Key_Return):
            if indexes := self.selectedIndexes():
                self.view(indexes[0])
                return event.accept()
        elif key == int(Qt.Key.Key_Delete):
            self.delete()
            return event.accept()
        if key == int(Qt.Key.Key_Escape):
            self.clearSelection()
            return event.accept()
        return super().keyPressEvent(event)

    def view(self, index: QModelIndex) -> None:
        """What to do when a file or folder was clicked on the tree.

        Parameters
        ----------
        index : QModelIndex
            The index of the file or folder in the tree,

        """
        path = Path(self.filePath(index))
        if path.is_dir():
            if not self.isExpanded(index):
                return self.expand(index)
            return self.collapse(index)

        editor.setFocus() if (editor := self.window.tabView.createTab(path)) else ...

    def setSelectedIndex(self, widget) -> None:
        if widget and (path := getattr(widget, "path", None)):
            return self.setCurrentIndex(self._systemModel.index(str(path)))
        self.setCurrentIndex(self._systemModel.modelIndex)

    def createContextMenu(self) -> None:
        """Creates a context menu when an index was right clicked."""
        self.menu = QMenu(self.window)
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

        if sys.platform == "win32":
            showInFolder = self.menu.addAction("Show in Folder")
            showInFolder.triggered.connect(self.showInFolder)

        hide = self.menu.addAction("Hide")
        hide.triggered.connect(self.hideIndex)
        self.menu.addSeparator()
        addFolder = self.menu.addAction("Add Folder to Tree View")
        addFolder.triggered.connect(lambda: self.window.menubar.openFolderTreeView())
        remove = self.menu.addAction("Remove from Tree View")
        remove.triggered.connect(self.deleteLater)

    def filePath(self, index: QModelIndex) -> str:
        """Used to get a file path. Uses :meth:`~FileSystemModel.filePath`

        Parameters
        ----------
        index : QModelIndex
            The model index of a file or folder in the tree.

        Returns
        -------
        str
            The path of a file
        """
        return self._systemModel.filePath(index)

    def setFilter(self, filters: QDir.Filter) -> None:
        """Sets the `FileSystemModel` filters

        Parameters
        ----------
        filters : QDir.Filter
            An enum of filters for the system model
        """
        return self._systemModel.setFilter(filters)

    def createFile(self) -> None:
        """Creates a new file."""
        if not self.currentFolder:
            indexes = self.selectedIndexes()
            if not indexes:
                return
            index = indexes[0]
        else:
            index = self.getCurrentIndex()
        if not self._systemModel.isDir(index):
            index = index.parent()
        path = self._systemModel.createFile(index)
        self.window.tabView.createTab(path)
        self.fileCreated.emit(path)

    def createFolder(self) -> None:
        """Creates a new folder"""
        if not self.currentFolder:
            indexes = self.selectedIndexes()
            if not indexes:
                return
            index = indexes[0]
        else:
            index = self.getCurrentIndex()
        if not self._systemModel.isDir(index):
            index = index.parent()
        self._systemModel.createFolder(index)

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

    def closeFolder(self) -> None:
        """Closes the workspace if open"""
        self.changeFolder(None) if self.currentFolder else ...

    def rename(self) -> None:
        """Renames a folder or file"""
        index = self.getCurrentIndex()
        name, ok = QInputDialog.getText(
            self, "Rename", "Rename", QLineEdit.EchoMode.Normal, index.data()
        )
        if not name or not ok or name == index.data():
            return
        path = Path(self.filePath(index)).absolute()
        counter = 0
        names = name.split(".")
        while True:
            try:
                newPath = path.rename(f"{path.parent}/{name}").absolute()
                break
            except FileExistsError:
                counter += 1
                name = f"{names[0]} ({counter}).{'.'.join(names[1:])}"
        window = self.window
        if newPath.is_file():
            for editor in window.tabView:
                if editor.path == path:
                    window.tabView.setTabText(editor, name)
                    editor._watcher.removePath(str(editor.path))
                    editor.path = newPath
                    editor._watcher.addPath(str(editor.path))
                    break
            return

        for editor in window.tabView:
            if editor.path.is_relative_to(path):
                editor._watcher.removePath(str(editor.path))
                editor.path = Path(
                    str(newPath) + str(editor.path).split(str(path))[1]
                ).absolute()
                editor._watcher.addPath(str(editor.path))

    def delete(self) -> None:
        """Deletes a folder or file"""
        selectedIndexes = self.selectedIndexes()
        if not selectedIndexes:
            return
        index = selectedIndexes[0]
        if self._systemModel.isDir(index):
            path = self._systemModel.filePath(index)
            if not QDir(path).removeRecursively():
                dialog = QMessageBox(self.window)
                dialog.setWindowTitle("Cipher")
                dialog.setText(f"Failed to remove delete {path}")
                dialog.exec()
        else:
            self._systemModel.remove(index)

    def setFolder(self, path: Path | None) -> None:
        if self.currentFolder:
            self._workspaceSettings.removePath(str(self.currentFolder))
        self.setRootIndex(self._systemModel.setRootPath(path))
        if path:
            self._workspaceSettings.addPath(str(Path(self.settingsPath)))

    def changeFolder(self, path: Path | None) -> None:
        """Changes the workspace and triggers :attr:`workspaceChanged`

        Parameters
        ----------
        folderPath: :class:`~typing.Optional[str]`
            The path of the folder to open. Pass None to close the folder
        """
        if path and not path.exists():
            path = None
        self.setFolder(path)
        self.workspaceChanged.emit(path)
        self.updateSettings(True)

    def updateSettings(self, changeFolder: bool = False) -> None:
        """Updates the user settings

        Parameters
        ----------
        changeFolder: :class:`bool`
            Whether the workspace is changing or not, by default False
        """
        globalSettings = self.getGlobalSettings()
        workSpacesettings = self.getWorkspaceSettings()
        window = self.window
        if changeFolder:
            window.tabView.openTabs(
                workSpacesettings["currentFile"], workSpacesettings["openedFiles"]
            )
        showHidden = workSpacesettings.get(
            "showHidden", globalSettings.get("showHidden", False)
        )
        window.settings["showHidden"] = showHidden
        window.settings["username"] = workSpacesettings.get(
            "username", globalSettings.get("username")
        )
        window.settings["password"] = workSpacesettings.get(
            "password", globalSettings.get("password")
        )
        window.settings["search-pattern"] = workSpacesettings.get(
            "search-pattern", globalSettings.get("search-pattern", [])
        )
        window.settings["search-pattern"] = (
            []
            if not isinstance(window.settings["search-pattern"], list)
            else window.settings["search-pattern"]
        )
        window.settings["search-exclude"] = workSpacesettings.get(
            "search-exclude", globalSettings.get("search-exclude", [])
        )
        window.settings["search-exclude"] = (
            []
            if not isinstance(window.settings["search-exclude"], list)
            else window.settings["search-exclude"]
        )
        hiddenPaths = window.settings["hiddenPaths"]
        window.settings["hiddenPaths"] = [
            "/".join([self._systemModel.rootPath(), *str(path).split("\\")])
            for path in list(
                {
                    *workSpacesettings.get("hiddenPaths", []),
                    *globalSettings.get("hiddenPaths", []),
                }
            )
        ]
        for path in set(hiddenPaths).difference(set(window.settings["hiddenPaths"])):
            file = self._systemModel.index(path)
            self.setRowHidden(file.row(), file.parent(), False)
        if showHidden:
            for path in window.settings["hiddenPaths"]:
                file = self._systemModel.index(path)
                self.setRowHidden(file.row(), file.parent(), False)
        else:
            for path in window.settings["hiddenPaths"]:
                file = self._systemModel.index(path)
                self.setRowHidden(file.row(), file.parent(), True)
        filters = QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
        if showHidden:
            filters = filters | QDir.Filter.Hidden
        self.setFilter(filters)
        if self.currentFolder:
            for path in workSpacesettings.get("additionalPaths", []):
                if (path := Path(path)).exists():
                    window.fileManager.addTreeView(path)

    def copyPath(self) -> None:
        """Copies the path of an index"""
        cb = QApplication.clipboard()
        cb.clear()
        cb.setText(self.filePath(self.getCurrentIndex()))

    if sys.platform == "win32":

        def showInFolder(self) -> None:
            """Opens the file or folder in the file explorer"""
            subprocess.run(
                f'explorer /select,"{Path(self.filePath(self.getCurrentIndex()))}"',
                creationflags=0x08000000,
            )

    def hideIndex(self) -> None:
        """Hides the index. Will return when the editor is restarted. Note: For a permanant solution, edit the global or workspace settings."""
        files = self.selectedIndexes()
        if not files:
            return
        file = files[0]
        self.setRowHidden(file.row(), file.parent(), True)
        if self.currentFolder:
            path = Path(self._systemModel.filePath(file)).relative_to(
                self.currentFolder
            )
            settings = self.getWorkspaceSettings()
            if not (hiddenPaths := settings.get("hiddenPaths"), []):
                settings["hiddenPaths"] = hiddenPaths
            hiddenPaths.append(str(path))
            with open(f"{self.currentFolder}/.cipher/settings.json", "w") as f:
                json.dump(settings, f, indent=4)

    def findIndex(self, path: str) -> QModelIndex:
        return self._systemModel.index(path)

    def getCurrentIndex(self) -> QModelIndex:
        """Gets the current selected index. If no index is selected, returns the index of the workspace.

        Returns
        -------
        QModelIndex
            The model index of the selection
        """
        indexes = self.selectedIndexes()
        if not indexes or self.filePath(self._systemModel.modelIndex) not in self.filePath(indexes[0]):  # fmt:skip
            return self._systemModel.modelIndex
        return indexes[0]

    def getCurrentSettings(self) -> dict[str, Any]:
        """Returns either the workspace of global settings

        Returns
        -------
        dict[str, Any]
        """
        with open(self.settingsPath) as f:
            return json.load(f)

    def getGlobalSettings(self) -> dict[str, Any]:
        """Returns global settings

        Returns
        -------
        dict[str, Any]
        """
        with open(f"{self.window.localAppData}/settings.json") as f:
            return json.load(f)

    def getWorkspaceSettings(self) -> dict[str, Union[str, Any]]:
        """Returns workspace settings

        Returns
        -------
        dict[str, Any]
        """
        if not self.currentFolder:
            return {"project": None, "currentFile": None, "openedFiles": []}
        path = Path(f"{self.currentFolder}/.cipher").absolute()
        if not path.exists():
            path.mkdir()
            if sys.platform == "win32":
                with open(f"{path}/run.bat", "w") as f:
                    f.write("@echo off\nEXIT")
            else:
                with open(f"{path}/run.sh", "w") as f:
                    f.write("")

        path = Path(f"{path}/settings.json").absolute()
        if not path.exists():
            with open(path, "w") as f:
                json.dump(
                    {"project": None, "currentFile": None, "openedFiles": []},
                    f,
                    indent=4,
                )

        with open(path) as f:
            return json.load(f)

    def saveWorkspaceFiles(self, currentFile: Path, files: Iterable[Editor]) -> None:
        """Saves the open files when the workspace is changed

        Parameters
        ----------
        currentFile : `~pathlib.Path`
            The current tab
        files : Iterable[Editor]
            All tabs that are currently open
        """
        settings = self.getWorkspaceSettings()
        settings["currentFile"] = str(currentFile) if currentFile else None
        settings["openedFiles"] = tuple(str(widget.path) for widget in files)
        settings["additionalPaths"] = [
            str(path) for path in self.window.fileManager.getPaths()
        ]
        with open(f"{self.currentFolder}/.cipher/settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def saveSettings(self) -> None:
        """Saves the workspace when the window is closed. If another instance of the window is open, the function returns"""
        if not self.window.isMainWindow():
            return
        settings = self.getGlobalSettings()
        settings["lastFolder"] = str(self.currentFolder) if self.currentFolder else None
        window = self.window
        with open(f"{window.localAppData}/settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        if self.currentFolder:
            self.saveWorkspaceFiles(
                window.currentFile.path if window.currentFile else None,
                window.tabView.tabList,
            )


class MainTreeView(TreeView):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.updateSettings()

    def createContextMenu(self) -> None:
        super().createContextMenu()
        window = self.window

        def changeFolder():
            folder = QFileDialog.getExistingDirectory(
                self, "Pick a Folder", "C:/", options=QFileDialog().options()
            )
            if not folder:
                return
            path = Path(folder)
            if window.fileManager.hasPath(path):
                return
            self.setFolder(path)

        self.menu.removeAction(self.menu.actions()[-1])
        changeDir = self.menu.addAction("Change Folder")
        changeDir.triggered.connect(changeFolder)
