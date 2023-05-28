from cipher.ext.event import *
from cipher.ext.extension import *
from pypresence import Presence, exceptions as exec
from pathlib import Path
from typing import Optional
import time
import logging
import os


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
fileHandler = logging.FileHandler(f"{os.path.dirname(__file__)}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)

__all__ = ("RPC",)


class RPC(Extension):
    times = {}
    imgs = {".py": "python", ".pyi": "python", "c++": "cplusplus"}

    def __init__(self, **kwargs) -> None:
        self.window = kwargs.get("window")
        self._loop = self.window._loop
        self.rpc = Presence("1044002439906476063", loop=self._loop)
        self.rpc.connect()

    def update(self, folder: Optional[Path], widget) -> None:
        if not widget:
            return self.rpc.clear()
        name = widget.objectName()
        folder = folder.name if folder else None
        suffix = widget.path.suffix
        smallImage = self.imgs.get(suffix)
        workingTime = self.times.get(widget.path)
        if not workingTime:
            workingTime = time.time()
            self.times[widget.path] = workingTime
        try:
            self.rpc.update(
                state=f"Workspace: {folder}",
                details=f"Editing {name}",
                start=workingTime,
                small_image=smallImage,
                large_image="editor",
                large_text="Cipher",
                small_text=name,
            )
        except exec.InvalidID:
            self.rpc.close()
            self.rpc = Presence("1044002439906476063", loop=self._loop)
            self.rpc.connect()
            self.rpc.update(
                state=f"Workspace: {folder}",
                details=f"Editing {name}",
                start=workingTime,
                large_image="editor",
                large_text="Cipher",
            )

    @event()
    def onReady(self, folder: Optional[Path], widget) -> None:
        self.update(folder, widget)

    @event()
    def onWorkspaceChanged(self, _: Optional[Path]) -> None:
        self.times = {}

    @event()
    def widgetChanged(self, folder: Optional[Path], widget) -> None:
        self.update(folder, widget)

    @event()
    def onClose(self) -> None:
        if not self.rpc:
            return
        self.rpc.clear()

    @onReady.error
    def onReadyError(self, error: Exception, *args, **kwargs) -> None:
        if isinstance(error, AttributeError):
            return
        logger.error(f"RPC updateError - {error.__class__}: {error}")
        try:
            self.rpc.clear()
        except RuntimeError:
            pass

    @widgetChanged.error
    def widgetChangedError(self, error: Exception, *args, **kwargs) -> None:
        if isinstance(error, AttributeError):
            return
        if isinstance(error, exec.InvalidID):
            self.rpc.close()
            return self.rpc.connect()
        logger.error(f"RPC updateError - {error.__class__}: {error}")
        try:
            self.rpc.clear()
        except RuntimeError:
            pass

    @onClose.error
    def onCloseError(self, error: Exception, *args, **kwargs) -> None:
        logger.error(f"RPC updateError - {error.__class__}: {error}")
