from __future__ import annotations
from typing import Any, List, TYPE_CHECKING, Optional

from importlib import import_module
from pathlib import Path
import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QMessageBox
from cipher.ext import Extension

if TYPE_CHECKING:
    from .window import Window


__all__ = ("ExtensionItem", "ExtensionList")


class ExtensionItem(QListWidgetItem):
    __slots__ = ("name", "path")

    def __init__(self, name: str, icon: str, path: Path, enabled: bool) -> None:
        super().__init__()
        self.name = name
        self.path = path
        self.enabled = enabled
        self.ext: Optional[Extension] = None

        self.setIcon(QIcon(icon))
        self.setText(f"{self.name} (Disabled)") if not enabled else ...

    def listWidget(self) -> ExtensionList:
        return super().listWidget()

    async def initialize(self) -> None:
        self.setText(f"{self.name} (Loading)")
        window = self.listWidget().window
        try:
            mod = import_module(f"extension.{self.path.name}")
            self.ext: Extension = await mod.run(window=window)
        except Exception as e:
            print(f"Failed to add Extension {self.name} - {e.__class__.__name__}: {e}")
            return self.setText(f"{self.name} (Disabled)")
        if not isinstance(self.ext, Extension):
            self.ext = None
            return self.setText(f"{self.name} (Disabled)")
        setText = lambda: self.setText(self.name)
        setText() if self.ext.isReady else self.ext.ready.connect(setText)

    def enable(self) -> None:
        with open(f"{self.path}/settings.json") as f:
            data = json.load(f)
        data["enabled"] = self.enabled = True
        with open(f"{self.path}/settings.json", "w") as f:
            json.dump(data, f, indent=4)
        self.listWidget().window.createTask(self.initialize())

    def reload(self) -> None:
        if self.enabled:
            self.setText(f"{self.name} (Disabled)")
            self.ext.unload()
            self.ext = None
        self.listWidget().window.createTask(self.initialize())

    def disable(self) -> None:
        with open(f"{self.path}/settings.json") as f:
            data = json.load(f)
        data["enabled"] = self.enabled = False
        with open(f"{self.path}/settings.json", "w") as f:
            json.dump(data, f, indent=4)
        self.ext.unload()
        self.ext = None
        self.setText(f"{self.name} (Disabled)")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


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
        self.itemClicked.connect(lambda item: window.tabView.createTab(item.path))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.createContextMenu()
        self.customContextMenuRequested.connect(
            lambda pos: self.menu.exec(self.viewport().mapToGlobal(pos))
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
                if ((item := self.item(i)) and item.ext)
            )
        )

    def createContextMenu(self):
        self.menu = QMenu(self._window)
        self.menu.setObjectName("ExtensionContextMenu")
        enabledisable = self.menu.addAction("Enable/Disable")
        enabledisable.triggered.connect(self.enabledisable)
        enabledisable = self.menu.addAction("Reload")
        enabledisable.triggered.connect(self.reload)

    def selectedItems(self) -> List[ExtensionItem]:
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
        item = ExtensionItem(name, icon, path, enabled)
        self.addItem(item)
        (await item.initialize()) if enabled else ...

    def enabledisable(self) -> None:
        index = self.selectedItems()
        if not index:
            return
        index = index[0]
        index.enable() if not index.enabled else index.disable()

    def reload(self) -> None:
        index = self.selectedItems()
        index[0].reload() if not index else ...
