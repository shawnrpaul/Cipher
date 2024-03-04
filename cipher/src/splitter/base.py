from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QSplitterHandle

if TYPE_CHECKING:
    from ..window import Window

__all__ = ("BaseSplitter",)


class BaseSplitter(QSplitter):
    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._window = window
        self.setMouseTracking(True)

    @property
    def window(self) -> Window:
        return self._window

    def createHandle(self) -> QSplitterHandle:
        handle = super().createHandle()
        handle.setAttribute(Qt.WidgetAttribute.WA_Hover)
        return handle
