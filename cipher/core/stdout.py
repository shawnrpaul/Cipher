from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import ServerApplication


class Stdout:
    def __init__(self, app: ServerApplication) -> None:
        self.application = app

    def write(self, text: str):
        for window in self.application._windows:
            window.logs.write(text)

    def flush(self) -> None:
        ...
