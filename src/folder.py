from pathlib import Path
from typing import Optional

__all__ = ("Folder",)


class Folder:
    def __init__(self, folder: Optional[str]) -> None:
        self.changeFolder(folder)

    def changeFolder(self, folder: Optional[str]) -> None:
        if not folder:
            self.folder = None
            return

        self.folder = Path(folder).absolute()
        if not self.folder.exists():
            self.folder = None

    def __str__(self) -> str:
        return str(self.folder)

    def __bool__(self) -> bool:
        return bool(self.folder)
