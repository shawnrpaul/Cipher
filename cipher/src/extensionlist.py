from __future__ import annotations
from typing import Any, TYPE_CHECKING, Optional

from importlib import import_module
from enum import IntEnum
from pathlib import Path
import json
import sys
import os

from PyQt6.QtGui import QContextMenuEvent, QIcon, QMouseEvent
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from cipher.ext import Extension

if TYPE_CHECKING:
    from .window import Window


__all__ = ("ExtensionItem", "ExtensionList")


class ExtensionItem(QListWidgetItem):
    class Status(IntEnum):
        LOADING = 1
        ENABLED = 2
        FAILED = 3
        DISABLED = 4

    def __init__(self, name: str, icon: str, path: Path) -> None:
        super().__init__()
        self.name = name
        self.path = path
        self.ext: Optional[Extension] = None

        self.setStatus(ExtensionItem.Status.DISABLED)
        self.setIcon(QIcon(icon))

    def __str__(self) -> str:
        return self.name

    def listWidget(self) -> ExtensionList:
        return super().listWidget()

    def setStatus(self, status: ExtensionItem.Status) -> None:
        self.status = status
        match status:
            case ExtensionItem.Status.LOADING:
                self.setText(f"{self.name} (Loading)")
            case ExtensionItem.Status.ENABLED:
                self.setText(self.name)
            case ExtensionItem.Status.FAILED:
                self.setText(f"{self.name} (Failed)")
            case ExtensionItem.Status.DISABLED:
                self.setText(f"{self.name} (Disabled)")
            case _:
                raise TypeError(
                    f"Status must be of type ExtensionItem.Status not {type(status)}"
                )

    async def initialize(self) -> None:
        self.setStatus(ExtensionItem.Status.LOADING)
        window = self.listWidget().window
        try:
            mod = import_module(f"extension.{self.path.name}")
            self.ext: Extension = await mod.run(window=window)
        except Exception as e:
            print(f"Failed to add Extension {self.name} - {e.__class__.__name__}: {e}")
            return self.setStatus(ExtensionItem.Status.FAILED)
        if not isinstance(self.ext, Extension):
            self.ext = None
            return self.setStatus(ExtensionItem.Status.FAILED)
        self.setStatus(ExtensionItem.Status.ENABLED)

    async def enable(self) -> None:
        with open(f"{self.path}/settings.json") as f:
            data = json.load(f)
        data["enabled"] = True
        with open(f"{self.path}/settings.json", "w") as f:
            json.dump(data, f, indent=4)
        await self.initialize()

    async def reload(self) -> None:
        match self.status:
            case ExtensionItem.Status.DISABLED:
                return await self.enable()
            case ExtensionItem.Status.ENABLED:
                await self.ext.unload()
                self.ext = None
                self._clear_modules()
                self.setStatus(ExtensionItem.Status.DISABLED)
        await self.initialize()

    async def disable(self) -> None:
        with open(f"{self.path}/settings.json") as f:
            data = json.load(f)
        data["enabled"] = False
        with open(f"{self.path}/settings.json", "w") as f:
            json.dump(data, f, indent=4)
        await self.ext.unload()
        self.ext = None
        self._clear_modules()
        self.setStatus(ExtensionItem.Status.DISABLED)

    def _clear_modules(self) -> None:
        mod_name = f"extension.{self.path.name}"
        for name in list(sys.modules):
            if name.startswith(mod_name):
                sys.modules.pop(name)


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
        self.addExtensions()

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
