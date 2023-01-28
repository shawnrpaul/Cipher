from .event import Event
from typing import Dict, List


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


class Extension(metaclass=ExtensionMeta):
    __events__: Dict[str, List[Event]]

    def __new__(cls, *args, **kwargs):
        self = super(Extension, cls).__new__(cls)
        return self

    def _inject(self) -> None:
        for events in self.__events__.values():
            for event in events:
                event.ext = self
