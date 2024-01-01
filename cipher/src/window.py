from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from pathlib import Path
import logging

from PyQt6.QtCore import QEvent, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMainWindow, QSystemTrayIcon

from .body import *
from .extensionlist import *
from .filemanager import *
from .git import *
from .menubar import *
from .search import *
from .sidebar import *
from .splitter import *
from .tabview import *
from .outputview import *
from .terminal import *
from .logs import *

if TYPE_CHECKING:
    from cipher.core import ServerApplication
    from .tab import Tab

__all__ = ("Window",)


class Window(QMainWindow):
    """The window object. Holds all other objects.

    Attributes
    ----------
    body: :class:`Body`
        The body of the editor
    tabView: :class:`TabWidget`
        Holds all the tabs
    fileManager: :class:`FileManager`
        The tree view of all files and folders
    extensionList: :class:`ExtensionList`
        The list view of all extensions
    git: :class:`Git`
        The tree view of (un)staged changes.
    search: :class:`GlobalSearch`
        The tree view of found phrases. Note: uses regex
    sidebar: :class:`Sidebar`
        The sidebar to select which view you want.
    menubar: :class:`Menubar`
        The menubar of the window
    notification: :class:`Notification`
        Sends a windows notification. Meant to be used by :class:`Extension`
    """

    closed = pyqtSignal()

    def __init__(self, app: ServerApplication) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self.application = app
        self._mainWindow = False
        self.settings = {
            "showHidden": False,
            "username": None,
            "password": None,
            "hiddenPaths": [],
            "search-pattern": [],
            "search-exclude": [],
        }

        self.tabView = TabView(self)
        self.fileManager = FileManager(self)
        self.extensionList = ExtensionList(self)
        self.git = Git(self)
        self.search = GlobalSearch(self)
        self.terminal = Terminal(self)
        self.logs = Logs(self)
        self.outputView = OutputView(self)
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)

        self.hsplit = HSplitter(self)
        self.fileSplitter = FileManagerSplitter(self)
        self.vsplit = VSplitter(self)
        self.vsplit.addWidget(self.tabView)
        self.vsplit.addWidget(self.outputView)
        self.hsplit.addWidget(self.fileSplitter)
        self.hsplit.addWidget(self.vsplit)

        body = Body(self)
        body.addWidget(self.sidebar)
        body.addWidget(self.hsplit)
        self.setMenuBar(self.menubar)
        self.setCentralWidget(body)

        self.systemTray = QSystemTrayIcon(self)
        self.systemTray.setIcon(QIcon(f"{self.localAppData}/icons/window.png"))

        originalWidth = self.screen().size().width()
        originalHeight = self.screen().size().height()
        width = int(originalWidth / 5.25)
        height = int(originalHeight / 2)

        self.hsplit.setSizes([width, originalWidth - width])
        self.vsplit.setSizes([height, height])

        self.showMaximized()

    @property
    def currentFolder(self) -> Optional[Path]:
        """Returns the `path` of current folder. Returns `None` if there isn't a current folder."""
        return self.fileManager.currentFolder

    @property
    def currentFile(self) -> Optional[Tab]:
        """Returns the current `Editor` tab. Returns `None` if there isn't a current tab."""
        return self.tabView.currentFile

    @property
    def localAppData(self) -> str:
        return self.application.localAppData

    @property
    def shortcut(self):
        return self.application._shortcut

    @property
    def styles(self):
        return self.application._styles

    @property
    def loop(self):
        return self.application.loop

    def isMainWindow(self) -> bool:
        return self._mainWindow

    def setMainWindow(self, main: bool = False) -> bool:
        self._mainWindow = main

    def createTask(self, coro) -> None:
        return self.application.createTask(coro)

    def resumeSession(self):
        settings = self.fileManager.getGlobalSettings()
        folder = settings.get("lastFolder")
        if folder and not Path(folder).absolute().exists():
            folder = None
        self.fileManager.changeFolder(folder)
        if self.currentFolder:
            settings = self.fileManager.getWorkspaceSettings()
            self.tabView.openTabs(
                settings.get("currentFile"), settings.get("openedFiles", [])
            )

    def event(self, event: QEvent) -> bool:
        if hasattr(self, "extensionList"):
            for ext in self.extensionList.extensions:
                self.application.sendEvent(ext, event)
        return super().event(event)

    def closeEvent(self, _: QCloseEvent) -> None:
        self.hide()
        self.closed.emit()
        self.fileManager.saveSettings()
        super().closeEvent(_)
        self.application.closeWindow(self)

    def log(self, text: str, level=logging.ERROR):
        self.logs.log(text, level)

    def showMessage(self, msg: str) -> None:
        self.systemTray.showMessage("Cipher", msg=msg, msecs=30_000)
