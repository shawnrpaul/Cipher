from typing import Any, Dict, List

from PyQt6.QtCore import QObject, pyqtSignal

from .event import Event

__all__ = ("Extension",)


class ExtensionMeta(type):
    __events__: Dict[str, List[Event]]

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        events = {}
        for base in reversed(self.__mro__):
            for value in base.__dict__.values():
                if isinstance(value, Event):
                    if not events.get(value.name):
                        events[value.name] = []
                    events[value.name].append(value)
        self.__events__ = events
        return self


class ExtensionCore(type(QObject), ExtensionMeta):
    ...


class Extension(QObject, metaclass=ExtensionCore):
    __events__: Dict[str, List[Event]] = {}
    ready = pyqtSignal()

    def __new__(cls, *args, **kwargs):
        self = super(Extension, cls).__new__(cls)
        for events in self.__events__.values():
            for event in events:
                event._instance = self

        return self

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent=parent)
        self.isReady = False

    def prepare(self):
        self.isReady = True
        self.ready.emit()
