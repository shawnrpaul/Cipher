from typing import Any, Callable
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from .worker import Worker

__all__ = ("Thread",)


class Thread(QThread):
    finished = pyqtSignal(object)

    def __init__(
        self, parent: QObject, func: Callable[..., Any], *args, **kwargs
    ) -> None:
        super().__init__(parent)
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self)
        self.started.connect(self.worker.run)
        self.worker.finished.connect(lambda ret: self.finished.emit(ret))
        self.worker.finished.connect(self.quit)
