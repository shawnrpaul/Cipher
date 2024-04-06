from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from ..splitter import VSplitter

if TYPE_CHECKING:
    from . import FileManager
    from .treeview import TreeView

__all__ = ("TreeViewSplitter",)


class TreeViewSplitter(VSplitter):
    def __init__(self, parent: FileManager) -> None:
        super().__init__(parent)
        self.setObjectName("TreeViewSplitter")
        treeView = parent.treeView
        self.addWidget(treeView)
        self.setFocusProxy(treeView)
        self.setContentsMargins(0, 0, 0, 0)

    def getPaths(self) -> list[Path]:
        return [self.widget(i).currentFolder for i in range(1, self.count())]

    def hasPath(self, path: Path) -> bool:
        for i in range(0, self.count()):
            treeView = self.widget(i)
            if treeView.currentFolder == path:
                return True
        return False

    def widget(self, index: int) -> TreeView:
        return super().widget(index)

    def addFileManager(self, treeView: TreeView) -> None:
        if self.hasPath(treeView.currentFolder):
            return
        self.addWidget(treeView)
