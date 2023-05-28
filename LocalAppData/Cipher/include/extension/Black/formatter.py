from cipher.ext.event import event
from cipher.ext.extension import Extension
import logging
import subprocess
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
fileHandler = logging.FileHandler(f"{os.path.dirname(__file__)}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class Black(Extension):
    def __init__(self, window) -> None:
        self.window = window

    @event()
    def onSave(self, editor) -> None:
        if editor.path.suffix != ".py":
            return
        editor.setReadOnly(True)
        subprocess.run(["black", str(editor.path)])
        editor.setReadOnly(False)

    @onSave.error
    def onSaveError(self, error: Exception, *args, **kwargs) -> None:
        logger.error(f"Black - {error.__class__}: {error}")
