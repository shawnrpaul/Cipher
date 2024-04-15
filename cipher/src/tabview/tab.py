from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from PyQt6.QtCore import QFileSystemWatcher
from PyQt6.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from ..window import Window

__all__ = ("Tab",)


class Tab:
    def __init__(self, window: Window, path: Path) -> None:
        self._window = window
        self.path = path
        self._watcher = QFileSystemWatcher()
        self._watcher.addPath(str(path))

    @property
    def window(self) -> Window:
        return self._window

    def focusInEvent(self, _) -> None:
        self.window.fileManager.setSelectedIndex(self)

    def saveFile(self) -> None:
        """Saves the editor"""
        self._watcher.removePath(str(self.path))
        self.path.write_text(self.text(), encoding="utf-8")
        self._watcher.addPath(str(self.path))

    def saveAs(self) -> None:
        """Saves the editor as a new file"""
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            str(self._window.currentFolder) if self._window.currentFolder else "C:/",
            "All Files (*);;Python files (*.py);;JSON files (*.json)",
        )
        if not file:
            return
        self._watcher.removePath(str(self.path))
        self.path = Path(file)
        self.path.write_text(self.text(), "utf-8")
        self._watcher.addPath(str(self.path))
        self._window.tabView.setTabText(
            self._window.tabView.currentIndex(), self.path.name
        )

    def text(self) -> str:
        raise NotImplemented

    def copy(self) -> None:
        raise NotImplemented

    def cut(self) -> None:
        raise NotImplemented

    def paste(self) -> None:
        raise NotImplemented

    def find(self) -> None:
        raise NotImplemented
