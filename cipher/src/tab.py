from __future__ import annotations

import sys
from copy import copy
from functools import singledispatchmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QTabWidget

from .editor import Editor

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("TabWidget",)


class TabWidget(QTabWidget):
    """The widget that holds all tabs

    Parameters
    ----------
    window : :class:`MainWindow`
        The window

    Attributes
    ----------
    tabOpened: :class:`pyqtSignal`
        A signal emitted when a new tab is opened
    """

    tabOpened = pyqtSignal(object)

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
        self.tabBar().tabMoved.connect(
            lambda __from, __to: self.__tabList.insert(
                __to, (self.__tabList.pop(__from))
            )
        )

    @property
    def currentFile(self) -> Optional[Editor]:
        """Returns the current :class:`Editor` if opened

        Alias for :func:`currentWidget` function
        Returns
        -------
        Optional[Editor]
            The current opened :class:`Editor` tab if opened.
        """
        return self.currentWidget()

    @property
    def tabList(self) -> List[Editor]:
        """Returns a copy of the tab list.

        Returns
        -------
        List[Editor]
            The list of editor that are currently open.
        """
        return copy(self.__tabList)

    def __iter__(self) -> Iterator[Editor]:
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
            self.setEditorTab(Path(path.toLocalFile()))
        return super().dropEvent(a0)

    def addTab(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> int:
        """Overrides the addTab function to add a tab to :attr:`tabList`

        Returns
        -------
        int
            The index of the new tab.
        """
        editor: Editor = kwargs.get("widget", args[0])
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
        editor: Editor = self.__tabList.pop(index)
        editor._watcher.removePath(str(editor.path))
        self.__stack.append(editor)
        return super().removeTab(index)

    @removeTab.register
    def _(self, widget: Editor) -> None:
        """An overloaded function of :func:`removeTab`. Adds the tab to the stack of closed tabs.

        Parameters
        ----------
        widget : Editor
            The editor to close
        """
        widget._watcher.removePath(str(widget.path))
        self.__stack.append(widget)
        self.__tabList.remove(widget)
        return super().removeTab(self.indexOf(widget))

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
    def _(self, widget: Editor, a1: str) -> None:
        """An overloaded version of :func:`setTabText`

        Parameters
        ----------
        widget : Editor
            The tab to reanme
        a1 : str
            The new name for the tab
        """
        return super().setTabText(self.indexOf(widget), a1)

    def setupTabs(self) -> None:
        """Reopen the tabs and open the folder the editor is opened"""
        if len(sys.argv) > 1:
            self.setEditorTab(Path(sys.argv[1]))
            return

        settings = self._window.fileManager.getGlobalSettings()
        folder = settings.get("lastFolder")
        if folder and not Path(folder).absolute().exists():
            folder = None
        self._window.fileManager.changeFolder(folder)
        if self._window.currentFolder:
            settings = self._window.fileManager.getWorkspaceSettings()
            self.openTabs(settings.get("currentFile"), settings.get("openedFiles", []))

    def openTabs(self, currentFile: str, files: List[str]) -> None:
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
            window = self.setEditorTab(Path(path))
            if currentFile == path:
                currentWidget = window

        if currentWidget:
            self.setCurrentWidget(currentWidget)

    def reopenTab(self) -> None:
        """Reopens the last closed tab. The tab will be skipped if it was reopened manually."""
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
        editor: Editor = self.currentWidget()
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

    def getEditorTab(self, path: Path) -> Optional[Editor]:
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

    def setEditorTab(self, path: Path) -> Editor:
        """Opens and sets the current tab

        Parameters
        ----------
        path : `Path`
            The absolute path of the file

        Returns
        -------
        Editor
            Returns the editor tab
        """
        path = path.absolute()
        if not path.exists():
            return
        if not path.is_file():
            return
        if self.isBinary(path):
            return
        if self.getEditorTab(path):
            return

        editor = Editor(window=self._window, path=path)
        editor.setText(path.read_text(encoding="utf-8"))
        self.addTab(editor, path.name)
        self.setCurrentWidget(editor)

        return editor
