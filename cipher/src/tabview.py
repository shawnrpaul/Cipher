from __future__ import annotations
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, Iterator, Optional, Tuple
from collections import deque
from pathlib import Path
from copy import copy

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QTabWidget

from .tab import Tab
from .editor import Editor
from .image import Image, GIF

if TYPE_CHECKING:
    from .window import Window

__all__ = ("TabView",)


class TabView(QTabWidget):
    """The widget that holds all tabs

    Parameters
    ----------
    window : :class:`Window`
        The window

    Attributes
    ----------
    tabOpened: :class:`pyqtSignal`
        A signal emitted when a new tab is opened
    """

    tabOpened = pyqtSignal(Tab)
    widgetChanged = pyqtSignal(object)
    tabClosed = pyqtSignal(Tab)

    def __init__(self, window: Window) -> None:
        super().__init__(window)
        self._window = window
        self.__tabList: list[Tab] = []
        self.__closedTabs: deque[Tab] = deque()
        self._tabCls: dict[str, Tab] = {
            ".gif": GIF,
            ".jpg": Image,
            ".webp": Image,
            ".png": Image,
        }
        self.setContentsMargins(0, 0, 0, 0)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setAcceptDrops(True)
        self.tabCloseRequested.connect(self.removeTab)
        self.tabBar().tabMoved.connect(
            lambda __from, __to: self.__tabList.insert(__to, (self.__tabList.pop(__from)))  # fmt: skip
        )
        self.currentChanged.connect(lambda _: self.widgetChanged.emit(self.currentFile))

    @property
    def window(self) -> Window:
        return self._window

    @property
    def currentFile(self) -> Optional[Tab]:
        """Returns the current :class:`Editor` if opened

        Alias for :func:`currentWidget` function
        Returns
        -------
        Optional[Tab]
            The current opened :class:`Tab` tab if opened.
        """
        return self.currentWidget()

    @property
    def tabList(self) -> list[Tab]:
        """Returns a copy of the tab list.

        Returns
        -------
        List[Editor]
            The list of editor that are currently open.
        """
        return copy(self.__tabList)

    def setTabCls(self, ext: str, cls: Tab) -> None:
        if not issubclass(cls, Tab):
            return
        self._tabCls[ext] = cls

    def __iter__(self) -> Iterator[Tab]:
        """Returns an iterator of a copy of the tablist"""
        return copy(self.__tabList).__iter__()

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        """Overrides the `dragEnterEvent` to accept a `dropEvent`

        Parameters
        ----------
        a0 : QDragEnterEvent
            The drag event when something is brought into the window.
        """
        a0.accept()

    def dropEvent(self, a0: QDropEvent) -> None:
        """Overrides the `dropEvent` add tab

        Parameters
        ----------
        a0 : QDropEvent
            The drop event when something is brought into the window.
        """
        urls = a0.mimeData().urls()
        if not urls:
            return
        path = urls[0]
        if path.isLocalFile():
            self.createTab(Path(path.toLocalFile()))
        return super().dropEvent(a0)

    def addTab(self, *args: Tuple[Any], **kwargs: dict[str, Any]) -> int:
        """Overrides the addTab function to add a tab to :attr:`tabList`

        Returns
        -------
        int
            The index of the new tab.
        """
        editor: Tab = kwargs.get("widget", args[0])
        self.__tabList.append(editor)
        ret = super().addTab(*args, **kwargs)
        self.tabOpened.emit(editor)
        return ret

    @singledispatchmethod
    def removeTab(self, index: int) -> None:
        """Closes a tab when the close button is pressed. Adds the tab to the stack of closed tabs.

        Parameters
        ----------
        index : int
            The index of the tab
        """
        tab = self.__tabList.pop(index)
        tab._watcher.removePath(str(tab.path))
        self.__closedTabs.append(tab)
        if len(self.__closedTabs) > 10:
            self.__closedTabs.popleft().deleteLater()
        self.tabClosed.emit(tab)
        super().removeTab(index)

    @removeTab.register
    def _(self, widget: Tab) -> None:
        """An overloaded function of :func:`removeTab`. Adds the tab to the stack of closed tabs.

        Parameters
        ----------
        widget : Editor
            The editor to close
        """
        widget._watcher.removePath(str(widget.path))
        self.__closedTabs.append(widget)
        self.__tabList.remove(widget)
        if len(self.__closedTabs) > 10:
            self.__closedTabs.popleft().deleteLater()
        self.tabClosed.emit(widget)
        super().removeTab(self.indexOf(widget))

    @singledispatchmethod
    def setTabText(self, index: int, a1: str) -> None:
        """Sets the tab text

        Parameters
        ----------
        index : int
            The index of the tab
        a1 : str
            The new name for the tab
        """
        return super().setTabText(index, a1)

    @setTabText.register
    def _(self, widget: Tab, a1: str) -> None:
        """An overloaded version of :func:`setTabText`

        Parameters
        ----------
        widget : Editor
            The tab to reanme
        a1 : str
            The new name for the tab
        """
        return super().setTabText(self.indexOf(widget), a1)

    def openTabs(self, currentFile: str, files: list[str]) -> None:
        """Opens all tabs. Used when the folder is changed.

        Parameters
        ----------
        currentFile : str
            The path of the tab that was last used
        files : List[str]
            A list of path that were opened when the folder was changed.
        """
        currentWidget = None
        for path in files:
            window = self.createTab(Path(path))
            if currentFile == path:
                currentWidget = window

        if currentWidget:
            self.setCurrentWidget(currentWidget)

    def reopenTab(self) -> None:
        """Reopens the last closed tab. The tab will be skipped if it was reopened manually."""
        while self.__closedTabs:
            editor = self.__closedTabs.pop()
            if not editor.path.exists():
                editor.deleteLater()
                continue
            for widget in self.__tabList:
                if editor.path == widget.path:
                    editor.deleteLater()
                    continue
            break
        else:
            return
        editor._watcher.addPath(str(editor.path))
        self.addTab(editor, editor.objectName())
        self.setCurrentWidget(editor)

    def changeTab(self) -> None:
        """Changes the tab. Used by :class:`Menubar` when Ctrl+Tab is pressed."""
        index = self.currentIndex() + 1
        if index >= len(self.tabList):
            index = 0
        self.setCurrentIndex(index)

    def closeCurrentTab(self) -> None:
        """Closes the current tab. Used by the window."""
        editor: Tab = self.currentWidget()
        if not editor:
            return
        editor._watcher.removePath(str(editor.path))
        self.removeTab(editor)

    def closeTabs(self) -> None:
        """Closes all tabs"""
        for _ in range(len(self.__tabList)):
            self.removeTab(0)

    def isBinary(self, path: Path) -> None:
        """Checks if the file is a binary file

        Parameters
        ----------
        path : `Path`
            The path of the file

        Returns
        -------
        bool
            Whether the file is binary.
        """
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def getTab(self, path: Path) -> Tab | None:
        """Gets the :class:`Editor` if opened

        Parameters
        ----------
        path : `Path`
            The path of the file

        Returns
        -------
        Optional[Editor]
            Returns the :class:`Editor` if found.
            Else returns `None`
        """
        for tab in self.__tabList:
            if tab.path == path:
                return tab
        return None

    def createTab(self, path: Path) -> Tab | None:
        path = path.absolute()
        if not path.exists() or not path.is_file():
            return
        if tab := self.getTab(path):
            return self.setCurrentWidget(tab)
        if cls := self._tabCls.get(path.suffix):
            tab = cls(self.window, path)
        else:
            if self.isBinary(path):
                return
            tab = Editor(window=self._window, path=path)
            tab.setText(path.read_text(encoding="utf-8"))
        self.addTab(tab, path.name)
        self.setCurrentWidget(tab)
        return tab
