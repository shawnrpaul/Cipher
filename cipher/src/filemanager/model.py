from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from PyQt6.QtCore import QObject, QModelIndex
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QInputDialog, QLineEdit

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
    def settingsPath(self) -> Path:
        """Returns the current settings.

        Returns
        -------
        :class:`Path`
            The path of global or workspace settings
        """
        return (
            Path(f"{self.currentFolder}/.cipher/settings.cipher").absolute()
            if self.currentFolder
            else Path(f"{self.window.localAppData}/settings.cipher").absolute()
        )

    def setRootPath(self, path: Path | None) -> QModelIndex:
        self.__currentFolder = path
        self.modelIndex = super().setRootPath(str(path) if path else None)
        return self.modelIndex

    def createFolder(self, index: QModelIndex) -> Path:
        name, ok = QInputDialog.getText(
            self, "Folder Name", "Give a name", QLineEdit.EchoMode.Normal, ""
        )
        if name and ok and name != index.data():
            index = self.mkdir(index, name)
        return Path(f"{self.filePath(index)}").absolute()

    def createFile(self, index: QModelIndex) -> Path:
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
        return path
