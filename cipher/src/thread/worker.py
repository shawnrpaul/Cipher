from typing import Any, Callable

from PyQt6.QtCore import QObject, pyqtSignal


class Worker(QObject):
    finished = pyqtSignal(object)

    def __init__(self, func: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            ret = self.func(*self.args, **self.kwargs)
        except Exception:
            ret = None
        self.finished.emit(ret)
