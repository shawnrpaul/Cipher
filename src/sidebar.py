from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from .extensionlist import ExtensionList
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy

if TYPE_CHECKING:
    from .window import MainWindow
    from .filemanager import FileManager

__all__ = ("Sidebar",)


class Explorer(QFrame):
    def __init__(self, fileManager: FileManager) -> None:
        super().__init__()
        self.setObjectName("Explorer")
        self.setLineWidth(1)
        self.setMaximumWidth(self.screen().size().width() // 5.3)
        self.setMinimumWidth(0)
        self.setBaseSize(100, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(fileManager)
        self.setLayout(layout)


class Sidebar(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self._window = window
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 10, 5, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
        )
        self.createFolder()
        self.createExtensionList()
        self.createSettings()
        self.setLayout(self._layout)

    def createFolder(self) -> None:
        self.explorer = Explorer(self._window.fileManager)
        folder = QLabel()
        folder.setPixmap(
            QPixmap(f"{self._window.localAppData}\\icons\\folder.svg").scaled(29, 29)
        )
        folder.setContentsMargins(3, 0, 0, 4)
        folder.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        folder.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        folder.mousePressEvent = self.folderMousePressEvent
        self._layout.addWidget(folder)

    def folderMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), Explorer):
            return self.explorer.setVisible(not self.explorer.isVisible())
        self._window.hsplit.replaceWidget(0, self.explorer)
        self.explorer.setVisible(True)

    def createExtensionList(self) -> None:
        extensions = QLabel()
        extensions.setPixmap(
            QPixmap(f"{self._window.localAppData}\\icons\\extensions.svg").scaled(
                29, 29
            )
        )
        extensions.setContentsMargins(2, 0, 0, 0)
        extensions.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        extensions.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        extensions.mousePressEvent = self.extensionsMousePressEvent
        self._layout.addWidget(extensions)

    def extensionsMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), ExtensionList):
            return self._window.extensions.setVisible(
                not self._window.extensions.isVisible()
            )
        self._window.hsplit.replaceWidget(0, self._window.extensions)
        self._window.extensions.setVisible(True)

    def createSettings(self) -> None:
        settings = QLabel()
        settings.setPixmap(
            QPixmap(f"{self._window.localAppData}\\icons\\settings.svg").scaled(31, 31)
        )
        settings.setContentsMargins(2, 5, 0, 0)
        settings.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        settings.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        settings.mousePressEvent = self.settingsMousePressEvent
        self._layout.addWidget(settings)

    def settingsMousePressEvent(self, _: QMouseEvent = None) -> None:
        path = Path(f"{self._window.localAppData}\\settings.json").absolute()
        if not path.exists():
            return
        self._window.setEditorTab(path)
