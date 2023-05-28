from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import traceback
from importlib import import_module
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Optional, Type

from PyQt6.QtCore import QFileSystemWatcher, Qt, QThreadPool
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QSplitter
from winotify import Notification

from ..ext.exceptions import EventTypeError
from ..ext.extension import Extension
from .body import *
from .extensionlist import *
from .filemanager import *
from .git import *
from .menubar import *
from .search import *
from .sidebar import *
from .tab import *
from .thread import *

if TYPE_CHECKING:
    from ..ext.event import Event
    from .editor import Editor

__all__ = ("run",)

# localAppData = os.path.join(os.getenv("LocalAppData"), "Cipher")
localAppData = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "LocalAppData",
    "Cipher",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s: %(message)s")
fileHandler = logging.FileHandler(f"{localAppData}\\logs.log")
fileHandler.setFormatter(format)
logger.addHandler(fileHandler)


class MainWindow(QMainWindow):
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

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self._threadPool = QThreadPool.globalInstance()
        self.localAppData = localAppData
        self.setWindowIcon(QIcon(f"{localAppData}\\icons\\window.png"))
        self.settings = {
            "showHidden": False,
            "username": None,
            "password": None,
            "hiddenPaths": [],
            "search-pattern": [],
            "search-exclude": [],
        }

        self.body = Body(self)
        self.tabView = TabWidget(self)
        self.fileManager = FileManager(self)
        self.extensionList = ExtensionList(self)
        self.git = Git(self)
        self.search = GlobalSearch(self)
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)
        self.notification = Notification(
            app_id="Cipher", title="Cipher", icon=f"{localAppData}\\icons\\window.png"
        )

        self.setMenuBar(self.menubar)
        self.body._layout.addWidget(self.sidebar)
        self._hsplit = QSplitter(Qt.Orientation.Horizontal)
        self._hsplit.addWidget(self.sidebar.explorer)
        self._hsplit.addWidget(self.tabView)
        self.body._layout.addWidget(self._hsplit)
        self.body.setLayout()
        self.setCentralWidget(self.body)

        originalWidth = self.screen().size().width()
        width = int(originalWidth / 5.07)

        self._hsplit.setSizes([width, originalWidth - width])

        styles = f"{localAppData}\\styles\\styles.qss"
        self._styles = QFileSystemWatcher(self)
        self._styles.addPath(styles)
        self._styles.fileChanged.connect(
            lambda: self.setStyleSheet(open(styles).read())
        )
        self.setStyleSheet(open(styles).read())

        sys.path.insert(0, f"{localAppData}\\include")
        sys.path.insert(0, f"{localAppData}\\site-packages")

        self.tabView.setupTabs()
        self.tabView.currentChanged.connect(self.widgetChanged)

        self._events: dict[str, list[Event]] = {}
        self._events["widgetChanged"] = []
        self._events["onTabOpened"] = []
        self._events["onWorkspaceChanged"] = []
        self._events["onSave"] = []
        self._events["onClose"] = []
        self.tabView.tabOpened.connect(self.onTabOpened)
        self.fileManager.onWorkspaceChanged.connect(self.onWorkspaceChanged)
        self.fileManager.onSave.connect(self.onSave)

        self._loop = asyncio.get_event_loop()
        Thread(self, self.addExtensions).start()
        self.showMaximized()

    @property
    def currentFolder(self) -> Optional[Path]:
        """Returns the `path` of current folder. Returns `None` if there isn't a current folder."""
        return self.fileManager.currentFolder

    @property
    def currentFile(self) -> Optional[Editor]:
        """Returns the current `Editor` tab. Returns `None` if there isn't a current tab."""
        return self.tabView.currentFile

    @property
    def menuBar(self) -> QMenuBar:
        """Overrides :class:`QMainWindow` menuBar function to return the :class:`QMenuBar` being used.

        Returns
        -------
        QMenuBar
            The :class:`QMenuBar` used by the editor
        """
        return self.menubar

    def addExtensions(self) -> None:
        """Gets the list of extension folder and starts a thread to activate each extension.
        Meant to be used by :class:`MainWindow`
        """
        extensions = f"{localAppData}\\include\\extension"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}\\{folder}").absolute()
            settings = Path(f"{path}\\settings.json").absolute()
            self._threadPool.start(Runnable(self.addExtension, path, settings))

    def addExtension(self, path: Path, settings: Path) -> None:
        """Adds the :class:`Extension`
        Meant to be used by :class:`MainWindow`

        Parameters
        ----------
        path : `Path`
            The path of the extension folder
        settings : `Path`
            The path of the extension settings.
            If the extension is disabled in settings, the :class:`Extension` won't be added.
        """
        if not path.exists() or not settings.exists():
            return
        with open(settings) as f:
            data: dict[str, Any] = json.load(f)
        name = data.get("name")
        if not name:
            return

        icon = f"{path}\\icon.ico"
        if not Path(icon).exists():
            icon = f"{self.localAppData}\\icons\\blank.ico"

        if data.get("enabled"):
            try:
                mod = import_module(f"extension.{path.name}.run")
                obj = mod.run(window=self)
            except EventTypeError:
                return
            except Exception as e:
                logger.error(f"Failed to add Extension - {e.__class__.__name__}: {e}")
                name = f"{name} (Disabled)"
                self.extensionList.addItem(ExtensionItem(name, icon, settings))
                return
            if not isinstance(obj, Extension):
                return
            self._events["widgetChanged"].extend(
                obj.__events__.get("widgetChanged", [])
            )
            self._events["onWorkspaceChanged"].extend(
                obj.__events__.get("onWorkspaceChanged", [])
            )
            self._events["onTabOpened"].extend(obj.__events__.get("onTabOpened", []))
            self._events["onSave"].extend(obj.__events__.get("onSave", []))
            self._events["onClose"].extend(obj.__events__.get("onClose", []))
            onReady = obj.__events__.get("onReady", [])
            self.extensionList.addItem(ExtensionItem(name, icon, settings))
        else:
            name = f"{name} (Disabled)"
            self.extensionList.addItem(ExtensionItem(name, icon, settings))

        for func in onReady:
            self._threadPool.start(Runnable(func, self.currentFolder, self.currentFile))

    def onWorkspaceChanged(self) -> None:
        """An event triggered when `currentFolder` is changed"""
        for func in self._events.get("onWorkspaceChanged", []):
            self._threadPool.start(Runnable(func, self.currentFolder))

    def widgetChanged(self, _: int) -> None:
        """An event triggered when `currentFile` is changed"""
        for func in self._events.get("widgetChanged", []):
            self._threadPool.start(Runnable(func, self.currentFolder, self.currentFile))

    def onTabOpened(self, editor):
        """An event triggered when :class:`Editor` is opened"""
        for func in self._events.get("onTabOpened", []):
            self._threadPool.start(Runnable(func, editor))

    def onSave(self) -> None:
        """An event triggered when :class:`Editor` is saved"""
        for func in self._events.get("onSave", []):
            self._threadPool.start(Runnable(func, self.currentFile))

    def close(self) -> None:
        """An event triggered when :class:`MainWindow` is closed"""
        for func in self._events.get("onClose", []):
            self._threadPool.start(Runnable(func))


def excepthook(
    func: Callable[[Type[BaseException], Optional[BaseException], TracebackType], Any],
    app: QApplication,
) -> Any:
    def log(
        exc_type: Type[BaseException],
        exc_value: Optional[BaseException],
        exc_tb: TracebackType,
    ) -> Any:
        tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
        cwd = Path(os.path.dirname(os.path.dirname(__file__))).absolute()
        for frame in tb.stack[::-1]:
            file = Path(frame.filename).absolute()
            if file.is_relative_to(cwd):
                line = frame.lineno
                break
        logger.error(f"{file.name}({line}) - {exc_type.__name__}: {exc_value}")
        app.quit()
        return func(exc_type, exc_value, exc_tb)

    return log


def run() -> None:
    app = QApplication([])
    sys.excepthook = excepthook(sys.excepthook, app)
    window = MainWindow()
    app.aboutToQuit.connect(window.close)
    app.aboutToQuit.connect(window.fileManager.saveSettings)
    app.exec()
