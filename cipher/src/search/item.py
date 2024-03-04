from pathlib import Path

from PyQt6.QtGui import QStandardItem

__all__ = ("SearchMatch", "SearchFile")


class SearchFile(QStandardItem):
    def __init__(self, file: str):
        super().__init__(file)
        self.setEditable(False)


class SearchMatch(QStandardItem):
    def __init__(self, text: str, path: Path, index: int, cs):
        super().__init__(text)
        self.path = path
        self._index = index
        self.cs = cs
        self.setEditable(False)
