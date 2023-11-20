from __future__ import annotations
from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING
import inspect


__all__ = ("event",)

if TYPE_CHECKING:
    from .extension import Extension


class Event:
    """The function to run certain event.

    Parameters
    ----------
    name: str
    func: `~typing.Callable[..., ~typing.Any]`
    """

    def __init__(self, *, name: str = None, func: Callable[..., Any] = None) -> None:
        self.name: str = name if name else func.__name__
        self._instance: Extension = None
        self.func = func
        self._error: Optional[Callable[..., Any]] = None

    async def invoke(self, *args, **kwargs) -> None:
        try:
            await self.func(self._instance, *args, **kwargs)
        except Exception as e:
            if self._error:
                try:
                    return self._error(self._instance, e, *args, **kwargs)
                except Exception:
                    ...

    def __call__(self, *args: Tuple[Any], **kwargs: Dict[Any, Any]) -> Any:
        window = self._instance.window
        window.createTask(self.invoke(*args, **kwargs))

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async")
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
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async.")
        return Event(name=name, func=func)

    return decorator
