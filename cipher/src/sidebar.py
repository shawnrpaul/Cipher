from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout

from .splitter import VSplitter
from .extensionlist import ExtensionList
from .git import Git
from .search import GlobalSearch

if TYPE_CHECKING:
    from .window import Window

__all__ = ("Sidebar",)


class Sidebar(QFrame):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.setObjectName("Sidebar")
        self._window = window
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

        self.createSettings()
        self.createFolder()
        self.createExtensionList()
        self.createSearch()
        self.createGitList()

    @property
    def window(self) -> Window:
        return self._window

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()

    def createSettings(self) -> None:
        settings = QLabel(self)
        settings.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/settings.svg").scaled(31, 31)
        )
        settings.setContentsMargins(2, 5, 0, 0)
        settings.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        settings.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        settings.mousePressEvent = self.settingsMousePressEvent
        self.layout.addWidget(settings)

    def createFolder(self) -> None:
        folder = QLabel(self)
        folder.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/folder.svg").scaled(29, 29)
        )
        folder.setContentsMargins(3, 0, 0, 4)
        folder.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        folder.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        folder.mousePressEvent = self.folderMousePressEvent
        self.addWidget(folder)

    def folderMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), VSplitter):
            self._window.fileSplitter.setVisible(
                not self._window.fileSplitter.isVisible()
            )
        else:
            self._window.hsplit.replaceWidget(0, self._window.fileSplitter)
            self._window.fileSplitter.setVisible(True)
        self._window.fileManager.setFocus() if self._window.fileManager.isVisible() else ...

    def createExtensionList(self) -> None:
        extensions = QLabel(self)
        extensions.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/extensions.svg").scaled(29, 29)
        )
        extensions.setContentsMargins(2, 0, 0, 0)
        extensions.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        extensions.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        extensions.mousePressEvent = self.extensionListMousePressEvent
        self.addWidget(extensions)

    def extensionListMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), ExtensionList):
            self._window.extensionList.setVisible(
                not self._window.extensionList.isVisible()
            )
        else:
            self._window.hsplit.replaceWidget(0, self._window.extensionList)
            self._window.extensionList.setVisible(True)
        self._window.extensionList.setFocus()

    def createSearch(self) -> None:
        search = QLabel(self)
        search.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/search.svg").scaled(26, 26)
        )
        search.setContentsMargins(4, 5, 0, 0)
        search.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        search.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        search.mousePressEvent = self.searchMousePressEvent
        self.addWidget(search)

    def searchMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), GlobalSearch):
            self._window.search.setVisible(not self._window.search.isVisible())
        else:
            self._window.hsplit.replaceWidget(0, self._window.search)
            self._window.search.setVisible(True)
        self._window.search.textBox.selectAll()
        self._window.search.textBox.setFocus()

    def createGitList(self) -> None:
        git = QLabel(self)
        git.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/git.svg").scaled(32, 32)
        )
        git.setContentsMargins(1, 4, 0, 0)
        git.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        git.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        git.mousePressEvent = self.gitMousePressEvent
        self.addWidget(git)

    def gitMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window.hsplit.widget(0), Git):
            self._window.git.setVisible(not self._window.git.isVisible())
        else:
            self._window.hsplit.replaceWidget(0, self._window.git)
            self._window.git.setVisible(True)
        self._window.git.setFocus()

    def settingsMousePressEvent(self, _: QMouseEvent = None) -> None:
        path = self._window.fileManager.settingsPath
        if not path.exists():
            return
        self._window.tabView.createTab(path)

    def addWidget(self, widget: QWidget):
        layout = self.layout
        layout.insertWidget(layout.count() - 1, widget)
