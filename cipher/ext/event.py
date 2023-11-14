from types import FunctionType
from typing import Any, Callable, Dict, Optional, Tuple
import asyncio
import inspect

from .exceptions import EventTypeError

__all__ = ("event",)


class Event:
    """The function to run certain event.

    Parameters
    ----------
    name: str
    func: `~typing.Callable[..., ~typing.Any]`
    """

    def __init__(self, *, name: str = None, func: Callable[..., Any] = None) -> None:
        self.name: str = name if name else func.__name__
        self._instance = None
        self.func = func
        self._error: Optional[Callable[..., Any]] = None

    def __call__(self, *args: Tuple[Any], **kwargs: Dict[Any, Any]) -> Any:
        try:
            if inspect.iscoroutinefunction(self.func):
                return asyncio.create_task(self.func(self._instance, *args, **kwargs))
            return self.func(self._instance, *args, **kwargs)
        except Exception as e:
            if self._error:
                try:
                    return self._error(self._instance, e, *args, **kwargs)
                except Exception:
                    ...

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._error = func
        return func


def event(name: str = None) -> Event:
    """Decorator to create an `Event` object

    Parameters
    ----------
    name : str, optional
        Name of the editor event. If not provided, the function name must be the event name. By default None

    Returns
    -------
    Event
        The event object
    """

    def decorator(func: Callable[..., Any]) -> Event:
        if not isinstance(func, FunctionType):
            raise EventTypeError("Object is not a function.")
        return Event(name=name, func=func)

    return decorator
