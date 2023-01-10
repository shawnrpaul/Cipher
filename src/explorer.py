from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Explorer",)


class Explorer(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Explorer")
        self.setLineWidth(1)
        self.setMaximumWidth(235)
        self.setMinimumWidth(0)
        self.setBaseSize(100, 0)
        self.resize(200, self.height())
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(window.fileManager)
        self.setLayout(layout)
