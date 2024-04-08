from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pathlib import Path
import json
import os

from PyQt6.QtGui import QContextMenuEvent, QMouseEvent
from PyQt6.QtWidgets import QListWidget, QMenu

from cipher.ext import Extension
from .item import ExtensionItem

if TYPE_CHECKING:
    from ..window import Window


__all__ = ("ExtensionList",)


class ExtensionList(QListWidget):
    """The list view of all :class:`Extension`

    Parameters
    ----------
    window: :class:`Window`

    Attributes
    ----------

    """

    def __init__(self, window: Window) -> None:
        super().__init__()
        self.setObjectName("ExtensionList")
        self._window = window
        self.setMaximumWidth(self.screen().size().width() // 2)
        self.itemClicked.connect(
            lambda item: window.tabView.createTab(Path(f"{item.path}/settings.json"))
        )
        window.started.connect(self.addExtensions)

    @property
    def window(self) -> Window:
        return self._window

    @property
    def extensions(self) -> tuple[Extension]:
        return tuple(
            (
                item.ext
                for i in range(self.count())
                if (
                    (item := self.item(i))
                    and item.status == ExtensionItem.Status.ENABLED
                )
            )
        )

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if not self.indexAt(e.pos()).data():
            self.clearSelection()
        return super().mousePressEvent(e)

    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        if not (indexes := self.selectedItems()):
            return
        index = indexes[0]
        menu = QMenu(self._window)
        menu.setObjectName("ExtensionContextMenu")

        enableExtension = menu.addAction("Enable Extension")
        enableExtension.triggered.connect(self.enableExtension)
        disableExtension = menu.addAction("Disable Extension")
        disableExtension.triggered.connect(self.disableExtension)
        reloadExtension = menu.addAction("Reload Extension")
        reloadExtension.triggered.connect(self.reloadExtension)
        menu.addSeparator()
        menu.addAction("Settings").triggered.connect(
            lambda: self.window.tabView.createTab(Path(f"{index.path}/settings.json"))
        )

        match index.status:
            case ExtensionItem.Status.LOADING:
                enableExtension.setEnabled(False)
                disableExtension.setEnabled(False)
                reloadExtension.setEnabled(False)
            case ExtensionItem.Status.ENABLED:
                enableExtension.setEnabled(False)
            case _:
                disableExtension.setEnabled(False)

        menu.exec(self.viewport().mapToGlobal(a0.pos()))

    def selectedItems(self) -> list[ExtensionItem]:
        return super().selectedItems()

    def addExtensions(self) -> None:
        extensions = f"{self.window.localAppData}/include/extension"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}/{folder}").absolute()
            if path.is_file():
                continue
            settings = Path(f"{path}/settings.json").absolute()
            if not settings.exists():
                continue
            self.window.createTask(self.addExtension(path, settings))

    async def addExtension(self, path: Path, settings: Path) -> None:
        """Adds the :class:`Extension`
        Meant to be used by :class:`Window`

        Parameters
        ----------
        path : `Path`
            The path of the extension folder
        settings : `Path`
            The path of the extension settings.
            If the extension is disabled in settings, the :class:`Extension` won't be added.
        """
        try:
            with open(settings) as f:
                data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError:
            return
        if not (name := data.get("name")):
            return
        icon = f"{path}/icon.ico"
        if not Path(icon).exists():
            icon = f"{self.window.localAppData}/icons/blank.ico"
        enabled = data.get("enabled")
        item = ExtensionItem(name, icon, path)
        self.addItem(item)
        (await item.initialize()) if enabled else ...

    def enableExtension(self) -> None:
        indexes = self.selectedItems()
        self.window.createTask(indexes[0].enable()) if indexes else ...

    def reloadExtension(self) -> None:
        indexes = self.selectedItems()
        self.window.createTask(indexes[0].reload()) if indexes else ...

    def disableExtension(self) -> None:
        indexes = self.selectedItems()
        self.window.createTask(indexes[0].disable()) if indexes else ...
