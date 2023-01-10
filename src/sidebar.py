from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from .explorer import Explorer
from .extensions import ExtensionList

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Sidebar",)


class Sidebar(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 10, 5, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
        )
        self.createFolder(window)
        self.createExtensionList(window)
        self.createSettings(window)
        self.setLayout(self._layout)

    def createFolder(self, window: MainWindow) -> None:
        folder = QLabel()
        folder.setPixmap(
            QPixmap(f"{window.localAppData}\\icons\\folder.svg").scaled(35, 38)
        )
        folder.mousePressEvent = lambda _: self.folderMousePressEvent(window, _)
        self._layout.addWidget(folder)

    def folderMousePressEvent(self, window: MainWindow, _: QMouseEvent) -> None:
        visible = window.explorer.isVisible()
        if isinstance(window.hsplit.widget(0), Explorer):
            return window.explorer.setVisible(not visible)
        window.hsplit.replaceWidget(0, window.explorer)
        window.explorer.setVisible(True)

    def createExtensionList(self, window: MainWindow) -> None:
        extensions = QLabel()
        extensions.setPixmap(
            QPixmap(f"{window.localAppData}\\icons\\extensions.svg").scaled(29, 29)
        )
        extensions.setContentsMargins(2, 0, 0, 0)
        extensions.mousePressEvent = lambda _: self.extensionsMousePressEvent(window, _)
        self._layout.addWidget(extensions)

    def extensionsMousePressEvent(self, window: MainWindow, _: QMouseEvent) -> None:
        visible = window.extensions.isVisible()
        if isinstance(window.hsplit.widget(0), ExtensionList):
            return window.extensions.setVisible(not visible)
        window.hsplit.replaceWidget(0, window.extensions)
        window.extensions.setVisible(True)

    def createSettings(self, window: MainWindow) -> None:
        settings = QLabel()
        settings.setPixmap(
            QPixmap(f"{window.localAppData}\\icons\\settings.svg").scaled(31, 31)
        )
        settings.setContentsMargins(2, 5, 0, 0)
        settings.mousePressEvent = lambda _: self.settingsMousePressEvent(window, _)
        self._layout.addWidget(settings)

    def settingsMousePressEvent(self, window: MainWindow, _: QMouseEvent) -> None:
        path = Path(f"{window.localAppData}\\settings.json").absolute()
        if not path.exists():
            return
        window.setEditorTab(path)
