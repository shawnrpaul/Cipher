from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PyQt6.QtGui import QIcon

if TYPE_CHECKING:
    from .window import MainWindow


__all__ = ("ExtensionItem", "ExtensionList")


class ExtensionItem(QListWidgetItem):
    __slots__ = ("name", "path")

    def __init__(self, name: str, icon: str, path: Path) -> None:
        super().__init__(QIcon(icon), name)
        self.name = name
        self.path = path

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


class ExtensionList(QListWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("ExtensionList")
        self.setMaximumWidth(235)
        self.resize(200, self.height())
        self.itemClicked.connect(lambda item: window.setEditorTab(item.path))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.createContextMenu(window)
        self.customContextMenuRequested.connect(
            lambda pos: self.menu.exec(self.viewport().mapToGlobal(pos))
        )

    def createContextMenu(self, window: MainWindow):
        self.menu = QMenu(window)
        self.menu.setObjectName("ExtensionContextMenu")
        uninstall = self.menu.addAction("Uninstall")
        uninstall.triggered.connect(self.uninstall)

    def uninstall(self) -> None:
        index = self.selectedItems()
        if not index:
            return
        index = index[0]
