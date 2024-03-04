from __future__ import annotations
from typing import TYPE_CHECKING
import re

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QSizePolicy, QTreeView

from ..thread import Thread
from .model import SearchModel
from .item import SearchMatch

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    from cipher import Window

__all__ = ("SearchView",)


class SearchView(QTreeView):
    def __init__(self, parent: QWidget, window: Window, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._window = window
        self.setObjectName("SearchView")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHeaderHidden(True)

        self.__searchModel = SearchModel(self, window)
        self.setModel(self.__searchModel)

        self.clicked.connect(self.view)

    def view(self, index: QModelIndex):
        item = self.__searchModel.itemFromIndex(index)
        if isinstance(item, SearchMatch):
            if not (editor := self._window.tabView.getTab(item.path)):
                editor = self._window.tabView.createTab(item.path)
            for i, match in enumerate(
                re.compile(rf"{item.text()}", item.cs).finditer(editor.text())
            ):
                if i == item._index:
                    start = editor.lineIndexFromPosition(match.start())
                    end = editor.lineIndexFromPosition(match.end())
                    return editor.setSelection(*start, *end)
        if self.isExpanded(index):
            return self.collapse(index)
        return self.expand(index)

    def search(self, text: str, case: bool = False):
        currentFolder = self._window.currentFolder
        pattern = self._window.settings["search-pattern"]
        exclude = self._window.settings["search-exclude"]
        thread = Thread(
            self, self.__searchModel.search, currentFolder, text, case, pattern, exclude
        )
        thread.finished.connect(self.expandAll)
        thread.start()
