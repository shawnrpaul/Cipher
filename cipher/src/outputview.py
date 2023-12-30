from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QTabWidget

if TYPE_CHECKING:
    from .window import Window

__all__ = ("OutputView",)


class OutputView(QTabWidget):
    def __init__(self, window: Window) -> None:
        super().__init__()
        self._window = window
        self.setTabsClosable(False)
        self.addTab(window.terminal, "Terminal")
        self.addTab(window.logs, "Logs")
        self.hide()
