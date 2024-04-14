from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout

from .icon import Icon
from ..splitter import VSplitter

if TYPE_CHECKING:
    from ..window import Window

__all__ = ("Sidebar",)


class Sidebar(QFrame):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.setObjectName("Sidebar")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)

        self._createIcons()

    @property
    def window(self) -> Window:
        return super().window()

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def _createIcons(self) -> None:
        self._createSettings()
        self._createFolder()

        extensions = self.createIcon(self.window.extensionList)
        extensions.setContentsMargins(2, 0, 0, 0)
        extensions.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/extensions.svg").scaled(29, 29)
        )

        search = self.createIcon(self.window.search)
        search.setContentsMargins(4, 5, 0, 0)
        search.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/search.svg").scaled(26, 26)
        )

    def _createSettings(self) -> None:
        def settingsMousePressEvent(ev: QMouseEvent = None) -> None:
            path = self.window.fileManager.settingsPath
            self.window.tabView.createTab(path)
            return ev.accept()

        settings = QLabel(self)
        settings.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/settings.svg").scaled(31, 31)
        )
        settings.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings.setContentsMargins(1, 0, 0, 10)
        settings.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        settings.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        settings.mousePressEvent = settingsMousePressEvent
        self.layout.addWidget(
            settings, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter
        )

    def _createFolder(self) -> None:
        window = self.window

        def folderMousePressEvent(ev: QMouseEvent) -> None:
            if isinstance(window.hsplit.widget(0), VSplitter):
                window.fileManager.setVisible(not window.fileManager)
            else:
                window.hsplit.replaceWidget(0, window.fileManager)
                window.fileManager.setVisible(True)
            (window.fileManager.setFocus() if window.fileManager.isVisible() else ...)
            return ev.accept()

        folder = QLabel(self)
        folder.setPixmap(
            QPixmap(f"{window.localAppData}/icons/folder.svg").scaled(29, 29)
        )
        folder.setContentsMargins(3, 0, 0, 4)
        folder.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        folder.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        folder.mousePressEvent = folderMousePressEvent
        self.addIcon(folder)

    def createIcon(self, widget: QWidget) -> Icon:
        icon = Icon(self, widget)
        self.addIcon(icon)
        return icon

    def addIcon(self, icon: Icon) -> None:
        layout = self.layout
        layout.insertWidget(layout.count() - 1, icon)

    def removeIcon(self, icon: Icon) -> None:
        self.layout.removeWidget(icon)
        icon.setParent(None)
