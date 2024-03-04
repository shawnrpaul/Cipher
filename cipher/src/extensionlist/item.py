from __future__ import annotations
from typing import TYPE_CHECKING

from importlib import import_module
from enum import IntEnum
from pathlib import Path
import json
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListWidgetItem
from cipher.ext import Extension

if TYPE_CHECKING:
    from . import ExtensionList

__all__ = ("ExtensionItem",)


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
        self.ext: Extension | None = None

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
