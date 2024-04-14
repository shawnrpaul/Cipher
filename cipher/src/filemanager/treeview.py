from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import subprocess
import os

from PyQt6.QtCore import QDir, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QTreeView,
)

from .model import FileSystemModel
from ..tabview import Tab

if TYPE_CHECKING:
    from ..window import Window

__all__ = ("TreeView",)


class TreeView(QTreeView):
    """The tree view of files and folders

    Parameters
    ----------
    window: :class:`Window`
        The code editor window

    Attributes
    ----------
    folderCreated: :class:`pyqtSignal`
        A signal emitted when the folder is created
    fileCreated: :class:`pyqtSignal`
        A signal emitted when the file is created
    fileSaved: :class:`pyqtSignal`
        A signal emitted when a file is saved
    """

    folderCreated = pyqtSignal(Path)
    fileCreated = pyqtSignal(Path)
    fileSaved = pyqtSignal(Tab)

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setObjectName("FileManager")
        systemModel = FileSystemModel(self)
        self._hiddenPaths = []
        self._createContextMenu()

        self.setModel(systemModel)
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
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.setHeaderHidden(True)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)

        self.fileCreated.connect(parent.fileCreated.emit)
        self.folderCreated.connect(parent.fileCreated.emit)
        self.fileCreated.connect(parent.fileCreated.emit)

    @property
    def window(self) -> Window:
        return super().window()

    @property
    def model(self) -> FileSystemModel:
        return super().model()

    systemModel = model

    @property
    def currentFolder(self) -> Path | None:
        """Returns the :class:`~pathlib.Path` if there is a workspace.

        Returns
        -------
        :class:`~typing.Optional[~pathlib.Path]`
            The path of the workspace
        """
        return self.systemModel.currentFolder

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
        model = self.systemModel
        if widget and (path := getattr(widget, "path", None)):
            return self.setCurrentIndex(model.index(str(path)))
        self.setCurrentIndex(model.modelIndex)

    def _createContextMenu(self) -> None:
        """Creates a context menu when an index was right clicked."""
        self.menu = QMenu(self.window)
        self.menu.setObjectName("FileContextMenu")

        self.menu.addAction("New Folder").triggered.connect(self.createFolder)
        self.menu.addAction("New File").triggered.connect(self.createFile)

        self.menu.addSeparator()
        self.menu.addAction("Rename").triggered.connect(self.rename)
        self.menu.addAction("Delete").triggered.connect(self.delete)

        self.menu.addSeparator()
        self.menu.addAction("Copy Path").triggered.connect(self.copyPath)

        if self.window.application.platformName() == "windows":

            def showInFolder() -> None:
                """Opens the file or folder in the file explorer"""
                subprocess.run(
                    f'explorer /select,"{Path(self.filePath(self.getCurrentIndex()))}"',
                    creationflags=0x08000000,
                )

            self.menu.addAction("Show in Folder").triggered.connect(showInFolder)

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
        return self.systemModel.filePath(index)

    def setFilter(self, filters: QDir.Filter) -> None:
        """Sets the `FileSystemModel` filters

        Parameters
        ----------
        filters : QDir.Filter
            An enum of filters for the system model
        """
        return self.systemModel.setFilter(filters)

    def createFile(self) -> None:
        """Creates a new file."""
        if not self.currentFolder:
            indexes = self.selectedIndexes()
            if not indexes:
                return
            index = indexes[0]
        else:
            index = self.getCurrentIndex()
        name, ok = QInputDialog.getText(
            self, "File Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        model = self.systemModel
        if not model.isDir(index):
            index = index.parent()
        path = model.createFile(index, name)
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
        name, ok = QInputDialog.getText(
            self, "Folder Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if not name or not ok:
            return
        model = self.systemModel
        if not model.isDir(index):
            index = index.parent()
        model.createFolder(index, name)

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
                newPath = path.rename(path.parent, name).absolute()
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
        model = self.systemModel
        path = self.filePath(index)
        if model.isDir(index):
            if QDir(path).removeRecursively():
                for editor in self.window.tabView:
                    if editor.path.is_relative_to(path):
                        self.window.tabView.removeTab(editor)
            else:
                dialog = QMessageBox(self.window)
                dialog.setWindowTitle("Cipher")
                dialog.setText(f"Failed to remove delete {path}")
                dialog.exec()
        else:
            if model.remove(index):
                for editor in self.window.tabView:
                    if editor.path.is_relative_to(path):
                        return self.window.tabView.removeTab(editor)

            dialog = QMessageBox(self.window)
            dialog.setWindowTitle("Cipher")
            dialog.setText(f"Failed to remove delete {path}")
            dialog.exec()

    def setFolder(self, path: Path | None) -> None:
        for hiddenPath in self._hiddenPaths:
            index = self.systemModel.index(hiddenPath)
            if self.isRowHidden(index.row(), index.parent()):
                self.setRowHidden(index.row(), index.parent(), False)
        self._hiddenPaths.clear()
        self.setRootIndex(self.systemModel.setRootPath(path))

    def updateSettings(self) -> None:
        window = self.window
        model = self.systemModel
        showHidden = window.settings["showHidden"]
        toHide = set(window.settings["hiddenPaths"]).difference(self._hiddenPaths)
        toUnhide = set(self._hiddenPaths).difference(window.settings["hiddenPaths"])
        self._hiddenPaths.extend(toHide)
        rootPath = model.rootPath()
        for path in toUnhide:
            index = model.index(os.path.join(rootPath, path))
            self.setRowHidden(index.row(), index.parent(), False)
            self._hiddenPaths.remove(path)
        for path in self._hiddenPaths:
            index = model.index(os.path.join(rootPath, path))
            if not self.isRowHidden(index.row(), index.parent()):
                self.setRowHidden(index.row(), index.parent(), True)
        if showHidden:
            for path in self._hiddenPaths:
                index = model.index(os.path.join(rootPath, path))
                self.setRowHidden(index.row(), index.parent(), False)
        filters = QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files
        if showHidden:
            filters = filters | QDir.Filter.Hidden
        self.setFilter(filters)

    def copyPath(self) -> None:
        """Copies the path of an index"""
        cb = self.window.clipboard
        cb.clear()
        cb.setText(self.filePath(self.getCurrentIndex()))

    def getCurrentIndex(self) -> QModelIndex:
        """Gets the current selected index. If no index is selected, returns the index of the workspace.

        Returns
        -------
        QModelIndex
            The model index of the selection
        """
        indexes = self.selectedIndexes()
        model = self.systemModel
        if not indexes or self.filePath(model.modelIndex) not in self.filePath(indexes[0]):  # fmt:skip
            return self.model.modelIndex
        return indexes[0]
