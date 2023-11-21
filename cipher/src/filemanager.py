from __future__ import annotations

import json
import subprocess
import sys
from copy import copy
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from PyQt6.QtCore import QDir, QFileSystemWatcher, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QFileSystemModel, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QTreeView,
)

from .editor import Editor
from .thread import Thread

if TYPE_CHECKING:
    from .window import Window

__all__ = ("FileManager",)


class FileSystemModel(QFileSystemModel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setRootPath(None)

    @property
    def currentFolder(self) -> Optional[Path]:
        return copy(self.__currentFolder)

    def setRootPath(self, path: Optional[Path]) -> QModelIndex:
        self.__currentFolder = path
        self.modelIndex = super().setRootPath(str(path) if path else None)
        return self.modelIndex


class FileManager(QTreeView):
    """The tree view of files and folders

    Parameters
    ----------
    window: :class:`Window`
        The code editor window

    Attributes
    ----------
    onWorkspaceChanged: :class:`pyqtSignal`
        A signal emitted when the workspace is changed
    folderCreated: :class:`pyqtSignal`
        A signal emitted when the folder is created
    fileCreated: :class:`pyqtSignal`
        A signal emitted when the file is created
    onSave: :class:`pyqtSignal`
        A signal emitted when a file is saved
    """

    onWorkspaceChanged = pyqtSignal(object)
    folderCreated = pyqtSignal(Path)
    fileCreated = pyqtSignal(Path)
    onSave = pyqtSignal(Editor)

    def __init__(self, window: Window, main: bool = True) -> None:
        super().__init__()
        self.setObjectName("FileManager")
        self._window = window
        self.createContextMenu(main)
        self.__systemModel = FileSystemModel()

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
        self.setDragDropMode(QTreeView.DragDropMode.DragDrop)

        self._globalSettings = QFileSystemWatcher(
            [f"{window.localAppData}/settings.json"], self
        )
        self._globalSettings.fileChanged.connect(lambda: self.updateSettings())
        self._workspaceSettings = QFileSystemWatcher(self)
        self._workspaceSettings.fileChanged.connect(lambda: self.updateSettings())

        self.window.tabView.widgetChanged.connect(
            lambda widget: self.setCurrentIndex(self.__systemModel.index(str(path)))
            if widget and (path := getattr(widget, "path", None))
            else ...
        )

        if main:
            self.updateSettings()

    @property
    def window(self) -> Window:
        return self._window

    @property
    def currentFolder(self) -> Optional[Path]:
        """Returns the :class:`~pathlib.Path` if there is a workspace.

        Returns
        -------
        :class:`~typing.Optional[~pathlib.Path]`
            The path of the workspace
        """
        return self.__systemModel.currentFolder

    @property
    def settingsPath(self) -> Path:
        """Returns the current settings.

        Returns
        -------
        :class:`Path`
            The path of global or workspace settings
        """
        return (
            Path(f"{self.__systemModel.currentFolder}/.cipher/settings.json").absolute()
            if self.__systemModel.currentFolder
            else Path(f"{self._window.localAppData}/settings.json").absolute()
        )

    def mousePressEvent(self, e: QMouseEvent):
        self.setFocus()
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

        editor.setFocus() if (editor := self._window.tabView.createTab(path)) else ...

    def createContextMenu(self, main: bool) -> None:
        """Creates a context menu when an index was right clicked."""
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

        if sys.platform == "win32":
            showInFolder = self.menu.addAction("Show in Folder")
            showInFolder.triggered.connect(self.showInFolder)

        hide = self.menu.addAction("Hide")
        hide.triggered.connect(self.hideIndex)
        self.menu.addSeparator()
        addFolder = self.menu.addAction("Add Folder to Tree View")
        addFolder.triggered.connect(lambda: self._window.menubar.openFolderTreeView())
        if not main:

            def changeFolder():
                folder = QFileDialog.getExistingDirectory(
                    self, "Pick a Folder", "C:/", options=QFileDialog().options()
                )
                if not folder:
                    return
                path = Path(folder)
                if self._window.fileSplitter.hasPath(path):
                    return
                self.setFolder(path)

            changeDir = self.menu.addAction("Change Folder")
            changeDir.triggered.connect(changeFolder)
            remove = self.menu.addAction("Remove from Tree View")
            remove.triggered.connect(
                lambda: self._window.fileSplitter.removeFileManager(self.currentFolder)
            )

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
        return self.__systemModel.filePath(index)

    def setFilter(self, filters: QDir.Filter) -> None:
        """Sets the `FileSystemModel` filters

        Parameters
        ----------
        filters : QDir.Filter
            An enum of filters for the system model
        """
        return self.__systemModel.setFilter(filters)

    def createFile(self) -> None:
        """Creates a new file."""
        if not self.currentFolder:
            index = self.selectedIndexes()
            if not index:
                return
            index = index[0]
        else:
            index = self.getIndex()
            if Path(self.filePath(index)).is_file():
                index = index.parent()
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        path = Path(f"{self.filePath(index)}/{name}").absolute()
        counter = 0
        name = str(path).split(".")
        while path.exists():
            counter += 1
            path = Path(f"{name[0]} ({counter}).{'.'.join(name[1:])}").absolute()
        path.write_text("", "utf-8")
        editor = Editor(window=self._window, path=path)
        index = self._window.tabView.addTab(editor, path.name)
        self._window.tabView.setCurrentIndex(index)
        self.fileCreated.emit(path)
        self._window.git.status()

    def createFolder(self) -> None:
        """Creates a new folder"""
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
        self._window.git.status()

    def openFile(self, filePath: Optional[str] = None) -> None:
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
        self._window.tabView.createTab(path)

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

        self.changeFolder(folder)

    def closeFolder(self) -> None:
        """Closes the workspace if open"""
        self.changeFolder(None) if self.currentFolder else ...

    def rename(self) -> None:
        """Renames a folder or file"""
        index = self.getIndex()
        name, ok = QInputDialog.getText(
            self, "Rename", "Rename", QLineEdit.EchoMode.Normal, index.data()
        )
        if not name or not ok or name == index.data():
            return
        path = Path(self.filePath(index)).absolute()
        newPath = path.rename(f"{path.parent}/{name}").absolute()
        self._window.git.status()
        if newPath.is_file():
            for editor in self._window.tabView:
                if editor.path == path:
                    self._window.tabView.setTabText(editor, name)
                    editor._watcher.removePath(str(editor.path))
                    editor.path = newPath
                    editor._watcher.addPath(str(editor.path))
                    break
            return

        for editor in self._window.tabView:
            if editor.path.is_relative_to(path):
                editor._watcher.removePath(str(editor.path))
                editor.path = Path(
                    str(newPath) + str(editor.path).split(str(path))[1]
                ).absolute()
                editor._watcher.addPath(str(editor.path))

    def __delete(self, path: Path) -> None:
        if path.is_file():
            for widget in self._window.tabView:
                if widget.path == path:
                    self._window.tabView.removeTab(widget)
                    widget._watcher.removePath(str(widget.path))
                    break
            try:
                return path.unlink()
            except PermissionError:
                return

        for widget in self._window.tabView:
            if widget.path.is_relative_to(str(path)):
                self._window.tabView.removeTab(widget)
                widget._watcher.removePath(str(widget.path))
        try:
            rmtree(path.absolute())
        except PermissionError:
            ...

    def delete(self) -> None:
        """Deletes a folder or file"""
        selectedIndexes = self.selectedIndexes()
        if not selectedIndexes:
            return
        index = selectedIndexes[0]
        path = Path(self.filePath(index)).absolute()
        if not path.exists():
            return
        self.collapse(index)
        thread = Thread(self, self.__delete, path)
        thread.finished.connect(self._window.git.status)
        thread.start()

    def setFolder(self, path: Optional[Path]) -> None:
        self.setRootIndex(self.__systemModel.setRootPath(path))

    def changeFolder(self, folderPath: Optional[str]) -> None:
        """Changes the workspace and triggers :attr:`onWorkspaceChanged`

        Parameters
        ----------
        folderPath: :class:`~typing.Optional[str]`
            The path of the folder to open. Pass None to close the folder
        """
        if folderPath == str(self.currentFolder):
            return
        if self.currentFolder:
            currentFile = (
                self._window.currentFile.path if self._window.currentFile else None
            )
            self.saveWorkspaceFiles(currentFile, copy(self._window.tabView.tabList))
            self._window.fileSplitter.clear()
            self._workspaceSettings.removePath(str(self.currentFolder))
        self._window.tabView.closeTabs()
        folder = Path(folderPath).absolute() if folderPath else None
        if folder and not folder.exists():
            folder = None
        self.setFolder(folder)
        if folder:
            self._workspaceSettings.addPath(str(Path(self.settingsPath)))
        self.onWorkspaceChanged.emit(folder)
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
        if changeFolder:
            self._window.tabView.openTabs(
                workSpacesettings["currentFile"], workSpacesettings["openedFiles"]
            )
        showHidden = workSpacesettings.get(
            "showHidden", globalSettings.get("showHidden", False)
        )
        self._window.settings["showHidden"] = showHidden
        self._window.settings["username"] = workSpacesettings.get(
            "username", globalSettings.get("username")
        )
        self._window.settings["password"] = workSpacesettings.get(
            "password", globalSettings.get("password")
        )
        self._window.settings["search-pattern"] = workSpacesettings.get(
            "search-pattern", globalSettings.get("search-pattern", [])
        )
        self._window.settings["search-pattern"] = (
            []
            if not isinstance(self._window.settings["search-pattern"], list)
            else self._window.settings["search-pattern"]
        )
        self._window.settings["search-exclude"] = workSpacesettings.get(
            "search-exclude", globalSettings.get("search-exclude", [])
        )
        self._window.settings["search-exclude"] = (
            []
            if not isinstance(self._window.settings["search-exclude"], list)
            else self._window.settings["search-exclude"]
        )
        hiddenPaths = self._window.settings["hiddenPaths"]
        self._window.settings["hiddenPaths"] = [
            "/".join([self.__systemModel.rootPath(), *str(path).split("\\")])
            for path in list(
                {
                    *workSpacesettings.get("hiddenPaths", []),
                    *globalSettings.get("hiddenPaths", []),
                }
            )
        ]
        for path in set(hiddenPaths).difference(
            set(self._window.settings["hiddenPaths"])
        ):
            file = self.__systemModel.index(path)
            self.setRowHidden(file.row(), file.parent(), False)
        if showHidden:
            for path in self._window.settings["hiddenPaths"]:
                file = self.__systemModel.index(path)
                self.setRowHidden(file.row(), file.parent(), False)
        else:
            for path in self._window.settings["hiddenPaths"]:
                file = self.__systemModel.index(path)
                self.setRowHidden(file.row(), file.parent(), True)
        filters = QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
        if showHidden:
            filters = filters | QDir.Filter.Hidden
        self.setFilter(filters)
        if self.currentFolder:
            for path in workSpacesettings.get("additionalPaths", []):
                if (path := Path(path)).exists():
                    self._window.fileSplitter.addFileManager(path)

    def copyPath(self) -> None:
        """Copies the path of an index"""
        cb = QApplication.clipboard()
        cb.clear()
        cb.setText(self.filePath(self.getIndex()))

    if sys.platform == "win32":

        def showInFolder(self) -> None:
            """Opens the file or folder in the file explorer"""
            subprocess.run(
                f'explorer /select,"{Path(self.filePath(self.getIndex()))}"',
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
            path = Path(self.__systemModel.filePath(file)).relative_to(
                self.currentFolder
            )
            settings = self.getWorkspaceSettings()
            if not (hiddenPaths := settings.get("hiddenPaths"), []):
                settings["hiddenPaths"] = hiddenPaths
            hiddenPaths.append(str(path))
            with open(f"{self.currentFolder}/.cipher/settings.json", "w") as f:
                json.dump(settings, f, indent=4)

    def getIndex(self) -> QModelIndex:
        """Gets the current selected index. If no index is selected, returns the index of the workspace.

        Returns
        -------
        QModelIndex
            The model index of the selection
        """
        index = self.selectedIndexes()
        if not index or self.filePath(
            self.__systemModel.modelIndex
        ) not in self.filePath(index[0]):
            return self.__systemModel.modelIndex
        return index[0]

    def getCurrentSettings(self) -> Dict[str, Any]:
        """Returns either the workspace of global settings

        Returns
        -------
        Dict[str, Any]
        """
        with open(self.settingsPath) as f:
            return json.load(f)

    def getGlobalSettings(self) -> Dict[str, Any]:
        """Returns global settings

        Returns
        -------
        Dict[str, Any]
        """
        with open(f"{self._window.localAppData}/settings.json") as f:
            return json.load(f)

    def getWorkspaceSettings(self) -> Dict[str, Union[str, Any]]:
        """Returns workspace settings

        Returns
        -------
        Dict[str, Any]
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
            str(path) for path in self._window.fileSplitter.getPaths()
        ]
        with open(f"{self.currentFolder}/.cipher/settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    def saveSettings(self) -> None:
        """Saves the workspace when the window is closed. If another instance of the window is open, the function returns"""
        if not self.window.isMainWindow():
            return
        settings = self.getGlobalSettings()
        settings["lastFolder"] = str(self.currentFolder) if self.currentFolder else None
        with open(f"{self._window.localAppData}/settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        if self.currentFolder:
            self.saveWorkspaceFiles(
                self._window.currentFile.path if self._window.currentFile else None,
                self._window.tabView.tabList,
            )
