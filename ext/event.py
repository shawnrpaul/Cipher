from .exceptions import EventTypeError
from types import FunctionType
from typing import Any, Callable, Dict, Optional, Tuple

__all__ = ("Event", "event")


class Event:
    def __init__(self, *, name: str = None, func: Callable[..., Any] = None) -> None:
        self.name: str = name if name else func.__name__
        self.ext: self = None
        self.func = func
        self._error: Optional[Callable[..., Any]] = None

    def __call__(self, *args: Tuple[Any], **kwargs: Dict[Any, Any]) -> Any:
        try:
            return self.func(self.ext, *args, **kwargs)
        except Exception as e:
            if self._error:
                try:
                    return self._error(self.ext, e, *args, **kwargs)
                except Exception:
                    pass

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._error = func
        return func


def event(name: str = None) -> Event:
    def decorator(func: Callable[..., Any]) -> Event:
        if not isinstance(func, FunctionType):
            raise EventTypeError("Object is not a function.")
        return Event(name=name, func=func)

    return decorator
