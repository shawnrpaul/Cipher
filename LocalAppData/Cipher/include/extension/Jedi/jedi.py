from cipher.ext.event import *
from cipher.ext.extension import *
from .autocomplete import PyAutoCompleter
import logging
import os


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
fileHandler = logging.FileHandler(f"{os.path.dirname(__file__)}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)

__all__ = ("RPC",)


class Jedi(Extension):
    def __init__(self, **kwargs) -> None:
        self.window = kwargs.get("window")
        for editor in self.window.tabView:
            PyAutoCompleter(
                editor, self.window.fileManager.getWorkspaceSettings().get("project")
            )

    @event(name="onTabOpened")
    def createAutoCompleter(self, editor):
        if editor.path.suffix != ".py":
            return
        PyAutoCompleter(
            editor, self.window.fileManager.getWorkspaceSettings().get("project")
        )
