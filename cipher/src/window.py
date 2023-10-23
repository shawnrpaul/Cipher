from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from PyQt6.QtCore import QFileSystemWatcher, QThreadPool, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMainWindow, QSystemTrayIcon

from .body import *
from .extensionlist import *
from .filemanager import *
from .git import *
from .menubar import *
from .search import *
from .sidebar import *
from .tabview import *
from .splitter import *
from .terminal import Terminal
from .thread import Runnable
from cipher.ext import Extension
from cipher.ext.exceptions import EventTypeError

if TYPE_CHECKING:
    from ..ext.event import Event
    from .editor import Editor

__all__ = ("MainWindow",)

if sys.platform == "win32":
    localAppData = os.path.join(os.getenv("LocalAppData"), "Cipher")
elif sys.platform == "linux":
    localAppData = os.path.join(os.getenv("HOME"), "Cipher")
else:
    raise NotADirectoryError("MacOS isn't Supported")

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
format = logging.Formatter("%(levelname)s:%(asctime)s: %(message)s")
fileHandler = logging.FileHandler(f"{localAppData}/logs.log")
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

    __extensions__: dict[str, Extension]
    onClose = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cipher")
        self._threadPool = QThreadPool.globalInstance()
        self.localAppData = localAppData
        self.setWindowIcon(QIcon(f"{localAppData}/icons/window.png"))
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
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)
        self.terminal = Terminal(self)

        self.hsplit = HSplitter(self)
        self.fileSplitter = FileManagerSplitter(self)
        self.vsplit = VSplitter(self)
        self.vsplit.addWidget(self.tabView)
        self.vsplit.addWidget(self.terminal)
        self.hsplit.addWidget(self.fileSplitter)
        self.hsplit.addWidget(self.vsplit)

        body = Body(self)
        body._layout.addWidget(self.sidebar)
        body._layout.addWidget(self.hsplit)
        body.setLayout()
        self.setMenuBar(self.menubar)
        self.setCentralWidget(body)

        self.systemTray = QSystemTrayIcon(self)
        self.systemTray.setIcon(QIcon(f"{localAppData}/icons/window.png"))

        originalWidth = self.screen().size().width()
        width = int(originalWidth / 5.25)

        self.hsplit.setSizes([width, originalWidth - width])

        styles = f"{localAppData}/styles/styles.qss"
        self._styles = QFileSystemWatcher(self)
        self._styles.addPath(styles)
        self._styles.fileChanged.connect(
            lambda: self.setStyleSheet(open(styles).read())
        )
        self.setStyleSheet(open(styles).read())
        self._shortcut = QFileSystemWatcher(
            [f"{self.localAppData}/shortcuts.json"], self
        )
        self._shortcut.fileChanged.connect(self.updateShortcuts)

        sys.path.insert(0, f"{localAppData}/include")
        sys.path.insert(0, f"{localAppData}/site-packages")

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
        self.addExtensions()
        self.showMaximized()

    @property
    def currentFolder(self) -> Optional[Path]:
        """Returns the `path` of current folder. Returns `None` if there isn't a current folder."""
        return self.fileManager.currentFolder

    @property
    def currentFile(self) -> Optional[Editor]:
        """Returns the current `Editor` tab. Returns `None` if there isn't a current tab."""
        return self.tabView.currentFile

    def addExtensions(self) -> None:
        """Gets the list of extension folder and starts a thread to activate each extension.
        Meant to be used by :class:`MainWindow`
        """
        self.__extensions__ = {}
        extensions = f"{localAppData}/include/extension"
        for folder in os.listdir(extensions):
            path = Path(f"{extensions}/{folder}").absolute()
            if path.is_file():
                continue
            settings = Path(f"{path}/settings.json").absolute()
            if not settings.exists():
                continue
            self.addExtension(path, settings)

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
        try:
            with open(settings) as f:
                data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError:
            return

        if not (name := data.get("name")):
            return

        icon = f"{path}/icon.ico"
        if not Path(icon).exists():
            icon = f"{localAppData}/icons/blank.ico"

        if not data.get("enabled"):
            return self.extensionList.addItem(ExtensionItem(name, icon, settings))

        try:
            mod = import_module(f"extension.{path.name}.run")
            ext = mod.run(window=self)
        except EventTypeError:
            return
        except Exception as e:
            logger.error(f"Failed to add Extension - {e.__class__.__name__}: {e}")
            name = f"{name} (Disabled)"
            return self.extensionList.addItem(ExtensionItem(name, icon, settings))
        if not isinstance(ext, Extension):
            return

        item = ExtensionItem(name, icon, settings, True)
        self.extensionList.addItem(item)

        def onExtReady():
            item.setText(name)
            onReady = ext.__events__.get("onReady", [])
            self._events["widgetChanged"].extend(
                ext.__events__.get("widgetChanged", [])
            )
            self._events["onWorkspaceChanged"].extend(
                ext.__events__.get("onWorkspaceChanged", [])
            )
            self._events["onTabOpened"].extend(ext.__events__.get("onTabOpened", []))
            self._events["onSave"].extend(ext.__events__.get("onSave", []))
            self._events["onClose"].extend(ext.__events__.get("onClose", []))
            for func in onReady:
                self._threadPool.start(
                    Runnable(func, self.currentFolder, self.currentFile)
                )

        onExtReady() if ext.isReady else ext.ready.connect(onExtReady)
        self.__extensions__[name] = ext

    def removeExtension(self, name: str) -> None:
        if not (ext := self.__extensions__.pop(name, None)):
            return
        for name, events in ext.__events__.items():
            if not (window_events := self._events.get(name)):
                continue
            for event in events:
                window_events.remove(event)

    def showMessage(self, msg: str) -> None:
        self.systemTray.showMessage("Cipher", msg=msg, msecs=30_000)

    def onWorkspaceChanged(self, path: Path) -> None:
        """An event triggered when `currentFolder` is changed"""
        for func in self._events.get("onWorkspaceChanged", []):
            self._threadPool.start(Runnable(func, self.currentFolder, path))

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

    def closeEvent(self, _: QCloseEvent) -> None:
        self.onClose.emit()

    def updateShortcuts(self) -> None:
        """Updates the shortcuts when `shortcuts.json` updates"""
        with open(f"{self.localAppData}/shortcuts.json") as f:
            shortcuts = json.load(f)
        for menu in self.menubar._menus:
            for action in menu.actions():
                if not (name := action.text()):
                    continue
                action.setShortcut(shortcuts.get(name, ""))
