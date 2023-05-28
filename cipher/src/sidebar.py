from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from .extensionlist import ExtensionList
from .git import Git
from .search import GlobalSearch

if TYPE_CHECKING:
    from .filemanager import FileManager
    from .window import MainWindow

__all__ = ("Sidebar",)


class Explorer(QFrame):
    """The Frame that holds :class:`FileManage`, :class:`ExtensionList`, :class:`Git`, :class:`GlobalSearch`"""

    def __init__(self, fileManager: FileManager) -> None:
        super().__init__()
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
        self.createSearch()
        self.createGitList()
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
        if isinstance(self._window._hsplit.widget(0), Explorer):
            return self.explorer.setVisible(not self.explorer.isVisible())
        self._window._hsplit.replaceWidget(0, self.explorer)
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
        extensions.mousePressEvent = self.extensionListMousePressEvent
        self._layout.addWidget(extensions)

    def extensionListMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window._hsplit.widget(0), ExtensionList):
            return self._window.extensionList.setVisible(
                not self._window.extensionList.isVisible()
            )
        self._window._hsplit.replaceWidget(0, self._window.extensionList)
        self._window.extensionList.setVisible(True)

    def createSearch(self) -> None:
        search = QLabel()
        search.setPixmap(
            QPixmap(f"{self._window.localAppData}\\icons\\search.svg").scaled(26, 26)
        )
        search.setContentsMargins(4, 5, 0, 0)
        search.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        search.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        search.mousePressEvent = self.searchMousePressEvent
        self._layout.addWidget(search)

    def searchMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window._hsplit.widget(0), GlobalSearch):
            return self._window.search.setVisible(not self._window.search.isVisible())
        self._window._hsplit.replaceWidget(0, self._window.search)
        self._window.search.textBox.selectAll()
        self._window.search.textBox.setFocus()
        self._window.search.setVisible(True)

    def createGitList(self) -> None:
        git = QLabel()
        git.setPixmap(
            QPixmap(f"{self._window.localAppData}\\icons\\git.svg").scaled(32, 32)
        )
        git.setContentsMargins(1, 4, 0, 0)
        git.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        git.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        git.mousePressEvent = self.gitMousePressEvent
        self._layout.addWidget(git)

    def gitMousePressEvent(self, _: QMouseEvent) -> None:
        if isinstance(self._window._hsplit.widget(0), Git):
            return self._window.git.setVisible(not self._window.git.isVisible())
        self._window._hsplit.replaceWidget(0, self._window.git)
        self._window.git.setVisible(True)

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
        path = self._window.fileManager.settingsPath
        if not path.exists():
            return
        self._window.tabView.setEditorTab(path)
