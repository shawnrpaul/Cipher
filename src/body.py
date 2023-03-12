from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Body",)


class Body(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Body")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def setLayout(self) -> None:
        return super().setLayout(self._layout)
