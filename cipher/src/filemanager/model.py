from pathlib import Path
from PyQt6.QtCore import QModelIndex
from PyQt6.QtGui import QFileSystemModel


class FileSystemModel(QFileSystemModel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setRootPath(None)
        self.setReadOnly(False)

    @property
    def currentFolder(self) -> Path | None:
        return self.__currentFolder

    def setRootPath(self, path: Path | None) -> QModelIndex:
        self.__currentFolder = path
        self.modelIndex = super().setRootPath(str(path) if path else None)
        return self.modelIndex
