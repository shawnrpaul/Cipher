from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import json

from PyQt6.QtWidgets import QFrame, QScrollArea, QVBoxLayout
from .option import ListOption, CheckBoxOption
from .view import SettingsView
from ..tab import Tab

if TYPE_CHECKING:
    from cipher.src import Window


class Settings(Tab, QFrame):
    def __init__(self, window: Window, path: Path) -> None:
        Tab.__init__(self, window, path)
        QFrame.__init__(self)

        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(SettingsView(path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scrollArea)
        self.setLayout(layout)
