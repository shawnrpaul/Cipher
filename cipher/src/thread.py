from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, QThread, pyqtSignal, pyqtSlot

from ..ext.event import Event

__all__ = ("Thread", "Runnable")


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, func: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            ...
        self.finished.emit()


class Thread(QThread):
    def __init__(self, parent, func: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__(parent)
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        self.worker.finished.connect(self.finished.emit)
        self.worker.finished.connect(self.quit)


class Runnable(QRunnable):
    def __init__(self, func: Event, *args, **kwargs) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.func(*self.args, **self.kwargs)
        except Exception:
            ...
