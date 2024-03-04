from __future__ import annotations
from typing import Any, Callable, Tuple, TYPE_CHECKING
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

    def __init__(self, func: Callable[..., Any] = None) -> None:
        self._instance: Extension = None
        self.func = func
        self._error: Callable[..., Any] | None = None

    async def invoke(self, *args, **kwargs) -> None:
        try:
            await self.func(self._instance, *args, **kwargs)
        except Exception as e:
            if self._error:
                try:
                    await self._error(self._instance, e, *args, **kwargs)
                except Exception:
                    ...

    def __call__(self, *args: Tuple[Any], **kwargs: dict[Any, Any]) -> Any:
        window = self._instance.window
        window.createTask(self.invoke(*args, **kwargs))

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async")
        self._error = func
        return func


def event(func: Callable[..., Any]) -> Event:
    """Decorator to create an `Event` object

    Returns
    -------
    Event
        The event object
    """

    if not inspect.iscoroutinefunction(func):
        raise TypeError("The function must be async.")
    return Event(func)
