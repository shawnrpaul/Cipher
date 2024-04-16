from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
import inspect
import traceback


__all__ = ("event", "asyncEvent")

if TYPE_CHECKING:
    from .extension import Extension


class Event:
    """The function to run certain event.

    Parameters
    ----------
    name: str
    func: `~typing.Callable[..., ~typing.Any]`
    """

    def __init__(self, *, name: str | None, func: Callable[...]) -> None:
        if name is None:
            name = func.__name__
        if not isinstance(name, str):
            name = str(name)

        self.name = name
        self.func = func
        self._instance: Extension = None
        self._error: Callable[..., Any] | None = None

    def invoke(self, *args, **kwargs) -> None:
        try:
            self.func(self._instance, *args, **kwargs)
        except Exception as e:
            window = self._instance.window
            if self._error:
                try:
                    self._error(self._instance, e, *args, **kwargs)
                except Exception as exc:
                    window.log(
                        f"Exception Occured in {self._error.__name__}: {exc.__class__.__name__} - {e}",
                        flush=True,
                    )
                    for trace in traceback.format_exception(type(exc), exc, exc.__traceback__):  # fmt: skip
                        window.log(trace)
            else:
                window.log(
                    f"Exception Occured in {self.name}: {exc.__class__.__name__} - {e}",
                    flush=True,
                )
                for trace in traceback.format_exception(type(e), e, e.__traceback__):
                    self._instance.window.log(trace)

    def __call__(self, *args: tuple[Any], **kwargs: dict[Any, Any]) -> None:
        self.invoke(*args, **kwargs)

    def error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async")
        self._error = func
        return func


class AsyncEvent(Event):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def invoke(self, *args, **kwargs) -> None:
        try:
            await self.func(self._instance, *args, **kwargs)
        except Exception as e:
            window = self._instance.window
            if self._error:
                try:
                    await self._error(self._instance, e, *args, **kwargs)
                except Exception as exc:
                    window.log(
                        f"Exception Occured in {self._error.__name__}: {exc.__class__.__name__} - {e}",
                        flush=True,
                    )
                    for trace in traceback.format_exception(type(exc), exc, exc.__traceback__):  # fmt: skip
                        window.log(trace)
            else:
                window.log(
                    f"Exception Occured in {self.name}: {exc.__class__.__name__} - {e}",
                    flush=True,
                )
                for trace in traceback.format_exception(type(e), e, e.__traceback__):
                    self._instance.window.log(trace)

    def __call__(self, *args: tuple[Any], **kwargs: dict[Any, Any]) -> None:
        window = self._instance.window
        window.createTask(self.invoke(*args, **kwargs))

    def error(self, func: Callable[...]) -> Callable[...]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async")
        self._error = func
        return func


def event(name: str = None):
    def wrapper(func: Callable[...]) -> Event:
        return Event(name=name, func=func)

    return wrapper


def asyncEvent(name: str = None):
    def wrapper(func: Callable[...]) -> AsyncEvent:
        """Decorator to create an `Event` object

        Returns
        -------
        Event
            The event object
        """

        if not inspect.iscoroutinefunction(func):
            raise TypeError("The function must be async.")
        return AsyncEvent(name=name, func=func)

    return wrapper
