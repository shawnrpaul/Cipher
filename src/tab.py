from __future__ import annotations
from .editor import Editor
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDropEvent, QDragEnterEvent
from PyQt6.QtWidgets import QTabWidget
from multipledispatch import dispatch
from copy import copy
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("TabWidget",)


class TabWidget(QTabWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.tabList: List[Editor] = []
        self._stack: List[Editor] = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setAcceptDrops(True)
        self.tabCloseRequested.connect(self.removeTab)
        self._fileDropped = window.fileDropped

    def __iter__(self) -> Iterator[Editor]:
        return copy(self.tabList).__iter__()

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        a0.accept()

    def dropEvent(self, a0: QDropEvent) -> None:
        self._fileDropped
        return super().dropEvent(a0)

    def changeTab(self) -> None:
        index = self.currentIndex() + 1
        if index >= len(self.tabList):
            index = 0
        self.setCurrentIndex(index)

    def reopenTab(self) -> None:
        if not self._stack:
            return
        editor = self._stack.pop()
        self.addTab(editor, editor.objectName())
        self.setCurrentWidget(editor)

    @dispatch(int, str)
    def setTabText(self, index: int, a1: str) -> None:
        return super().setTabText(index, a1)

    @dispatch(Editor, str)
    def setTabText(self, widget: Editor, a1: str) -> None:
        return super().setTabText(self.indexOf(widget), a1)

    def addTab(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> int:
        self.tabList.append(kwargs.get("widget", args[0]))
        return super().addTab(*args, **kwargs)

    @dispatch(int)
    def removeTab(self, index: int) -> None:
        self._stack.append(self.tabList.pop(index))
        return super().removeTab(index)

    @dispatch(Editor)
    def removeTab(self, widget: Editor) -> None:
        self._stack.append(widget)
        self.tabList.remove(widget)
        return super().removeTab(self.indexOf(widget))

    def closeTabs(self) -> None:
        for _ in range(len(self.tabList)):
            self.removeTab(0)
