from __future__ import annotations
from typing import Any, TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from .event import Event

if TYPE_CHECKING:
    from cipher import Window

__all__ = ("Extension",)


class AsyncMixin(type):
    async def __call__(cls, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        await self.__init__(*args, **kwargs)
        return self


class ExtensionMeta(type):
    __events__: list[Event]

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        events = []
        for base in reversed(self.__mro__):
            for value in base.__dict__.values():
                if isinstance(value, Event):
                    events.append(value)
        self.__events__ = events
        return self


class ExtensionCore(type(QObject), ExtensionMeta, AsyncMixin):
    ...


class Extension(QObject, metaclass=ExtensionCore):
    __events__: list[Event] = []

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        for event in self.__events__:
            event._instance = self
        return self

    def __init__(self, window: Window) -> None:
        super().__init__(parent=window)
        self.window = window

    def event(self, event: QEvent) -> bool:
        self.eventReceived(event)
        return super().event(event)

    def eventReceived(self, event: QEvent) -> None:
        type = event.type()
        if type == QEvent.Type.KeyPress:
            return self.keyPressEvent(event)
        if type == QEvent.Type.KeyRelease:
            return self.keyReleaseEvent(event)
        if type == QEvent.Type.MouseButtonPress:
            return self.mousePressEvent(event)
        if type == QEvent.Type.MouseButtonDblClick:
            return self.mouseDoubleClickEvent(event)
        if type == QEvent.Type.MouseButtonRelease:
            return self.mouseReleaseEvent(event)
        if type == QEvent.Type.MouseMove:
            return self.mouseMoveEvent(event)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        ...

    def keyReleaseEvent(self, a0: QKeyEvent) -> None:
        ...

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        ...

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        ...

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        ...

    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        ...

    async def unload(self) -> Any:
        for event in self.__events__:
            event._instance = None
        self.setParent(None)
