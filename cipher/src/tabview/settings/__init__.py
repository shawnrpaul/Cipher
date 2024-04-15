from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import json

from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout
from .view import SettingsView
from ..tab import Tab

if TYPE_CHECKING:
    from cipher.src import Window


class Settings(Tab, QFrame):
    def __init__(self, window: Window, path: Path) -> None:
        Tab.__init__(self, window, path)
        QFrame.__init__(self)

        self.view = SettingsView(path)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self.view)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scrollArea)
        self.setLayout(layout)

    def saveFile(self) -> None: ...

    def saveAs(self) -> None: ...

    def text(self) -> None: ...

    def copy(self) -> None: ...

    def cut(self) -> None: ...

    def paste(self) -> None: ...

    def find(self) -> None: ...
