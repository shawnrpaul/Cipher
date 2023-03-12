from __future__ import annotations
from typing import Any, Dict, Iterator, List, Tuple, TYPE_CHECKING, Optional
from multipledispatch import dispatch
from copy import copy
from pathlib import Path
import sys

from .editor import Editor
from PyQt6.QtGui import QDropEvent, QDragEnterEvent
from PyQt6.QtWidgets import QTabWidget

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("TabWidget",)


class TabWidget(QTabWidget):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self._window = window
        self.__tabList: List[Editor] = []
        self.__stack: List[Editor] = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setAcceptDrops(True)
        self.tabCloseRequested.connect(self.removeTab)

    @property
    def currentFile(self) -> Optional[Editor]:
        return self.currentWidget()

    @property
    def tabList(self) -> List[Editor]:
        return copy(self.__tabList)

    def __iter__(self) -> Iterator[Editor]:
        return copy(self.__tabList).__iter__()

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        a0.accept()

    def dropEvent(self, a0: QDropEvent) -> None:
        self._window.fileDropped(a0)
        return super().dropEvent(a0)

    @dispatch(int, str)
    def setTabText(self, index: int, a1: str) -> None:
        return super().setTabText(index, a1)

    @dispatch(Editor, str)
    def setTabText(self, widget: Editor, a1: str) -> None:
        return super().setTabText(self.indexOf(widget), a1)

    def addTab(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> int:
        self.__tabList.append(kwargs.get("widget", args[0]))
        return super().addTab(*args, **kwargs)

    @dispatch(int)
    def removeTab(self, index: int) -> None:
        self.__stack.append(self.__tabList.pop(index))
        return super().removeTab(index)

    @dispatch(Editor)
    def removeTab(self, widget: Editor) -> None:
        self.__stack.append(widget)
        self.__tabList.remove(widget)
        return super().removeTab(self.indexOf(widget))

    def setupTabs(self) -> None:
        if len(sys.argv) > 1:
            self._window.fileManager.changeFolder(None)
            self.currentFile = self.setEditorTab(Path(sys.argv[1]))
            return

        settings = self._window.fileManager.getSettings()
        folder = settings.get("lastFolder")
        if folder and not Path(folder).absolute().exists():
            folder = None
        self._window.fileManager.changeFolder(folder)
        if self._window.currentFolder:
            settings = self._window.fileManager.getWorkspaceSettings()
            self.openTabs(settings.get("currentFile"), settings.get("openedFiles"))

    def openTabs(self, currentFile: str, files: List[str]) -> None:
        currentWidget = None
        for path in files:
            window = self.setEditorTab(Path(path))
            if currentFile == path:
                currentWidget = window

        if currentWidget:
            self.setCurrentWidget(currentWidget)

    def reopenTab(self) -> None:
        while self.__stack:
            editor = self.__stack.pop()
            if not editor.path.exists():
                continue
            for widget in self.__tabList:
                if editor.path == widget.path:
                    continue
            break
        else:
            return
        self.addTab(editor, editor.objectName())
        self.setCurrentWidget(editor)

    def changeTab(self) -> None:
        index = self.currentIndex() + 1
        if index >= len(self.tabList):
            index = 0
        self.setCurrentIndex(index)

    def closeCurrentTab(self) -> None:
        editor = self.currentWidget()
        if not editor:
            return
        self.removeTab(editor)

    def closeTabs(self) -> None:
        for _ in range(len(self.__tabList)):
            self.removeTab(0)

    def isBinary(self, path) -> None:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def setEditorTab(self, path: Path) -> Editor:
        path = path.absolute()
        if not path.exists():
            return
        if not path.is_file():
            return
        if self.isBinary(path):
            return

        for widget in self.__tabList:
            if path == widget.path:
                return

        editor = Editor(window=self._window, path=path)
        editor.setText(path.read_text(encoding="utf-8"))
        self.addTab(editor, path.name)
        self.setCurrentWidget(editor)

        return editor
