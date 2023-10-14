from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QSizePolicy, QFrame, QSplitterHandle, QVBoxLayout

from .filemanager import FileManager

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("VSplitter", "HSplitter", "FileManagerSplitter")


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


class BaseSplitter(QSplitter):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.setMouseTracking(True)

    def createHandle(self) -> QSplitterHandle:
        handle = super().createHandle()
        handle.setAttribute(Qt.WidgetAttribute.WA_Hover)
        return handle


class HSplitter(BaseSplitter):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.setObjectName("HSplitter")
        self.setOrientation(Qt.Orientation.Horizontal)


class VSplitter(BaseSplitter):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.setObjectName("VSplitter")
        self.setOrientation(Qt.Orientation.Vertical)


class FileManagerSplitter(VSplitter):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.setObjectName("FileManagerSplitter")
        self.addWidget(Explorer(window.fileManager))

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

    def addFileManager(self, path: Path) -> None:
        for i in range(0, self.count()):
            explorer: Explorer = self.widget(i)
            if explorer.fileManager.currentFolder == path:
                return
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
