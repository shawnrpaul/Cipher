from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QFrame, QHBoxLayout, QSizePolicy

if TYPE_CHECKING:
    from . import Window

__all__ = ("Body",)


class Body(QFrame):
    """Body of the editor. Holds all the widgets"""

    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self.setObjectName("Body")
        self._window = window
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

    @property
    def window(self) -> Window:
        return self._window

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)
