from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtWidgets import QLabel

from .tab import Tab

if TYPE_CHECKING:
    from ..window import Window


class Image(Tab, QLabel):
    def __init__(self, window: Window, path: Path) -> None:
        Tab.__init__(self, window, path)
        QLabel.__init__(self)
        self._watcher.fileChanged.connect(self.setImage)
        self.setPixmap(QPixmap(str(path)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setImage(self) -> None:
        self.setPixmap(QPixmap(str(self.path)))


class GIF(Tab, QLabel):
    def __init__(self, window: Window, path: Path) -> None:
        Tab.__init__(self, window, path)
        QLabel.__init__(self)
        self._movie = QMovie(str(path))
        self.setMovie(self._movie)
        self._movie.start()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._watcher.fileChanged.connect(self.setVideo)

    def setVideo(self) -> None:
        self.setPixmap(QPixmap(str(self.path)))
