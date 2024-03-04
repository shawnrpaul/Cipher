from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import os
import re

from PyQt6.QtGui import QStandardItemModel
from .item import *

if TYPE_CHECKING:
    from cipher import Window

__all__ = ("SearchModel",)


class SearchModel(QStandardItemModel):
    def __init__(self, parent, window: Window):
        super().__init__(parent)
        self.rootNode = self.invisibleRootItem()
        self._window = window

    @property
    def window(self) -> Window:
        return self._window

    def isBinary(self, path: Path) -> None:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def recursiveSearch(
        self,
        folder: Path,
        currentFolder: Path,
        text: str,
        cs: re._FlagsType,
        pattern: list[str],
        excluded: list[str],
    ):
        for dirEntry in os.scandir(folder):
            if dirEntry.name in excluded:
                continue
            path = Path(dirEntry.path)
            if path.is_file():
                if pattern and path.suffix not in pattern:
                    continue
                editor = self._window.tabView.getTab(path)
                try:
                    found = tuple(
                        (
                            SearchMatch(match.group(), path, i, cs)
                            for i, match in enumerate(
                                re.compile(rf"{text}", cs).finditer(
                                    path.read_text("utf-8")
                                    if not editor
                                    else editor.text()
                                )
                            )
                        )
                    )
                    if not found:
                        continue
                    file = SearchFile(str(path.relative_to(currentFolder)))
                    file.appendRows(found)
                    self.appendRow(file)
                except Exception:
                    continue
            elif path.is_dir():
                self.recursiveSearch(path, currentFolder, text, cs, pattern, excluded)

    def search(
        self,
        currentFolder: Path,
        text: str,
        case: bool,
        pattern: list[str],
        excluded: list[str],
    ):
        self.clear()

        if not text or not currentFolder:
            return

        cs = re.IGNORECASE if not case else 0

        for dirEntry in os.scandir(currentFolder):
            if dirEntry.name in excluded:
                continue
            path = Path(dirEntry.path)
            if path.is_file():
                if pattern and path.suffix not in pattern:
                    continue
                editor = self._window.tabView.getTab(path)
                try:
                    found = tuple(
                        (
                            SearchMatch(match.group(), path, i)
                            for i, match in enumerate(
                                re.compile(rf"{text}", cs).finditer(
                                    path.read_text("utf-8")
                                    if not editor
                                    else editor.text()
                                )
                            )
                        )
                    )
                    if not found:
                        continue
                    file = SearchFile(str(path.relative_to(currentFolder)))
                    file.appendRows(found)
                    self.appendRow(file)
                except Exception:
                    continue
            elif path.is_dir():
                self.recursiveSearch(path, currentFolder, text, cs, pattern, excluded)
