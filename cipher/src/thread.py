from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, QThread, pyqtSignal, pyqtSlot

from cipher.ext.event import Event

__all__ = ("Thread", "Runnable")


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
        except Exception as e:
            ret = None
        self.finished.emit(ret)


class Thread(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, parent, func: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__(parent)
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        self.worker.finished.connect(lambda ret: self.finished.emit(ret))
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
