from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QFileSystemWatcher

if TYPE_CHECKING:
    from .window import MainWindow


class Tab:
    def __init__(self, window: MainWindow, path: Path) -> None:
        self._window = window
        self.path = path
        self._watcher = QFileSystemWatcher()
        self._watcher.addPath(str(path))

    @property
    def window(self) -> MainWindow:
        return self._window
