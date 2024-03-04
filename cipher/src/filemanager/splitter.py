from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from PyQt6.QtWidgets import QSizePolicy, QFrame, QVBoxLayout

from ..splitter import VSplitter

if TYPE_CHECKING:
    from . import FileManager
    from ..window import Window


class Explorer(QFrame):
    """The Frame that holds :class:`FileManager`"""

    def __init__(self, fileManager: FileManager) -> None:
        super().__init__()
        self.fileManager = fileManager
        self.setObjectName("Explorer")
        self.setLineWidth(1)
        self.setMaximumWidth(self.screen().size().width() // 2)
        self.setMinimumWidth(0)
        self.setBaseSize(100, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(fileManager)
        self.setLayout(layout)


class FileManagerSplitter(VSplitter):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.setObjectName("FileManagerSplitter")
        self.addWidget(Explorer(window.fileManager))
        self.setFocusProxy(window.fileManager)

    def getPaths(self) -> list[Path]:
        return [
            self.widget(i).fileManager.currentFolder for i in range(1, self.count())
        ]

    def hasPath(self, path: Path) -> bool:
        for i in range(0, self.count()):
            explorer: Explorer = self.widget(i)
            if explorer.fileManager.currentFolder == path:
                return True
        return False

    def widget(self, index: int) -> Explorer:
        return super().widget(index)

    def fileManager(self, index: int) -> FileManager:
        return self.widget(index).fileManager

    def addFileManager(self, path: Path) -> None:
        for i in range(0, self.count()):
            explorer: Explorer = self.widget(i)
            if explorer.fileManager.currentFolder == path:
                return

        from . import FileManager

        fileManager = FileManager(self._window, False)
        fileManager.setFolder(path)
        self.addWidget(Explorer(fileManager))

    def removeFileManager(self, path: Path) -> None:
        for i in range(1, self.count()):
            explorer: Explorer = self.widget(i)
            if explorer.fileManager.currentFolder == path:
                return explorer.deleteLater()

    def clear(self) -> None:
        for i in range(1, self.count()):
            self.widget(i).deleteLater()
