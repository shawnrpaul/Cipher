from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QEnterEvent, QMouseEvent
from PyQt6.QtWidgets import QWidget, QLabel

if TYPE_CHECKING:
    from cipher import Window, Sidebar

__all__ = ("Icon",)


class Icon(QLabel):
    def __init__(self, parent: Sidebar, widget: QWidget) -> None:
        super().__init__(parent)
        self.widget = widget

    @property
    def window(self) -> Window:
        return super().window()

    def enterEvent(self, event: QEnterEvent) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        return event.accept()

    def leaveEvent(self, a0: QEvent) -> None:
        self.setCursor(Qt.CursorShape.ArrowCursor)
        return a0.accept()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if isinstance(self.window.hsplit.widget(0), type(self.widget)):
            self.widget.setVisible(not self.widget.isVisible())
        else:
            self.window.hsplit.replaceWidget(0, self.widget)
            self.widget.setVisible(True)
        self.widget.setFocus() if self.widget.isVisible() else ...
        return ev.accept()
