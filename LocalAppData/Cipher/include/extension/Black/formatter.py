from ext.event import event
from ext.extension import Extension
import black
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s:%(message)s")
fileHandler = logging.FileHandler(f"{os.path.dirname(__file__)}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class Black(Extension):
    def __init__(self, *args, **kwargs) -> None:
        ...

    @event()
    def onSave(self, editor) -> None:
        if editor.path.suffix != ".py":
            return
        pos = editor.getCursorPosition()
        out = black.format_file_contents(
            editor.path.read_text("utf-8"), fast=False, mode=black.FileMode()
        )
        editor.path.write_text(out, encoding="utf-8")
        editor.setText(out)
        editor.setCursorPosition(*pos)

    @onSave.error
    def onSaveError(self, error: Exception, *args, **kwargs) -> None:
        if isinstance(error, black.NothingChanged) or isinstance(
            error, black.InvalidInput
        ):
            return
        logger.error(f"Black - {error.__class__}: {error}")
