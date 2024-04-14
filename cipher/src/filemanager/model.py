from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from PyQt6.QtCore import QObject, QModelIndex
from PyQt6.QtGui import QFileSystemModel

if TYPE_CHECKING:
    from .treeview import TreeView
    from cipher import Window


class FileSystemModel(QFileSystemModel):
    def __init__(self, parent: TreeView) -> None:
        super().__init__(parent)
        self.setRootPath(None)
        self.setReadOnly(False)

    @property
    def treeView(self) -> TreeView:
        return QObject.parent(self)

    @property
    def window(self) -> Window:
        return self.treeView.window

    @property
    def currentFolder(self) -> Path | None:
        return self.__currentFolder

    @property
    def modelIndex(self) -> QModelIndex:
        return self._modelIndex

    def setRootPath(self, path: Path | None) -> QModelIndex:
        self.__currentFolder = path
        self._modelIndex = super().setRootPath(str(path) if path else None)
        return self._modelIndex

    def createFolder(self, index: QModelIndex, name: str) -> Path | None:
        """Create a folder under the given index

        Parameters
        ----------
        index : QModelIndex
            The index to create the folder under
        name : str
            Name of the folder

        Returns
        -------
        Path
            The path of the folder
        """
        index = self.mkdir(index, name)
        return Path(f"{self.filePath(index)}").absolute()

    def createFile(self, index: QModelIndex, name: str) -> Path:
        """Creates a file under the given index

        Parameters
        ----------
        index : QModelIndex
            The index to add the file to
        name : str
            The name of the file

        Returns
        -------
        Path
            The path of the new file
        """
        path = Path(f"{self.filePath(index)}/{name}").absolute()
        counter = 0
        name = str(path).split(".")
        while path.exists():
            counter += 1
            path = Path(f"{name[0]} ({counter}).{'.'.join(name[1:])}").absolute()
        path.write_text("", "utf-8")
        return path
