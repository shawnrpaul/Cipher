from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QEnterEvent, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QWidget, QFrame, QLabel, QVBoxLayout

from .splitter import VSplitter

if TYPE_CHECKING:
    from .window import Window

__all__ = ("Sidebar",)


class SidebarIcon(QLabel):
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.widget = widget

    @property
    def window(self) -> Window:
        return super().window()

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        return event.accept()

    def leaveEvent(self, a0: QEvent) -> None:
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return a0.accept()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if isinstance(self.window.hsplit.widget(0), type(self.widget)):
            self.widget.setVisible(not self.widget.isVisible())
        else:
            self.window.hsplit.replaceWidget(0, self.widget)
            self.widget.setVisible(True)
        self.widget.setFocus() if self.widget.isVisible() else ...
        return ev.accept()


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

        self._createIcons()

    @property
    def window(self) -> Window:
        return self._window

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
            if not path.exists():
                return
            self._window.tabView.createTab(path)
            return ev.accept()

        settings = QLabel(self)
        settings.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/settings.svg").scaled(31, 31)
        )
        settings.setContentsMargins(2, 5, 0, 0)
        settings.enterEvent = lambda _: self.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        settings.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        settings.mousePressEvent = settingsMousePressEvent
        self.layout.addWidget(settings)

    def _createFolder(self) -> None:
        def folderMousePressEvent(ev: QMouseEvent) -> None:
            if isinstance(self._window.hsplit.widget(0), VSplitter):
                self._window.fileSplitter.setVisible(
                    not self._window.fileSplitter.isVisible()
                )
            else:
                self._window.hsplit.replaceWidget(0, self._window.fileSplitter)
                self._window.fileSplitter.setVisible(True)
            self._window.fileManager.setFocus() if self._window.fileManager.isVisible() else ...
            return ev.accept()

        folder = QLabel(self)
        folder.setPixmap(
            QPixmap(f"{self.window.localAppData}/icons/folder.svg").scaled(29, 29)
        )
        folder.setContentsMargins(3, 0, 0, 4)
        folder.enterEvent = lambda _: self.setCursor(Qt.CursorShape.PointingHandCursor)
        folder.leaveEvent = lambda _: self.setCursor(Qt.CursorShape.ArrowCursor)
        folder.mousePressEvent = folderMousePressEvent
        self.addIcon(folder)

    def createIcon(self, widget: QWidget) -> SidebarIcon:
        icon = SidebarIcon(widget)
        self.addIcon(icon)
        return icon

    def addIcon(self, label: SidebarIcon) -> None:
        layout = self.layout
        layout.insertWidget(layout.count() - 1, label)
        label.setParent(self)

    def removeIcon(self, label: SidebarIcon) -> None:
        self.layout.removeWidget(label)
        label.setParent(None)
