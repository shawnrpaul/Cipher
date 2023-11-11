from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import sys
import zipfile
from importlib import import_module
from pathlib import Path
from typing import Any, TYPE_CHECKING, Optional

import requests
from PyQt6.QtCore import QFileSystemWatcher, pyqtSignal
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
from .terminal import *
from .logs import *
from cipher.ext import Extension
from cipher.ext.exceptions import EventTypeError

if TYPE_CHECKING:
    from ..ext.event import Event
    from .editor import Editor

__all__ = ("MainWindow",)

if sys.platform == "win32":
    _env = os.getenv("LocalAppData")
    localAppData = os.path.join(_env, "Cipher")
elif sys.platform == "linux":
    _env = os.getenv("HOME")
    localAppData = os.path.join(_env, "Cipher")
else:
    raise NotADirectoryError("MacOS isn't Supported")

if not os.path.exists(localAppData):
    req = requests.get(
        "https://github.com/Srpboyz/Cipher/releases/download/v1.3.1/LocalAppData.zip"
    )
    req.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(req.content)) as zip_file:
        zip_file.extractall(_env)


logging.basicConfig(
    filename=f"{localAppData}/logs.log",
    format="%(levelname)s:%(asctime)s: %(message)s",
    level=logging.ERROR,
)


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
        self.localAppData = localAppData
        self.settings = {
            "showHidden": False,
            "username": None,
            "password": None,
            "hiddenPaths": [],
            "search-pattern": [],
            "search-exclude": [],
        }

        styles = f"{localAppData}/styles/styles.qss"
        self._styles = QFileSystemWatcher(self)
        self._styles.addPath(styles)
        self._styles.fileChanged.connect(
            lambda: self.setStyleSheet(open(styles).read())
        )
        self._shortcut = QFileSystemWatcher(
            [f"{self.localAppData}/shortcuts.json"], self
        )

        self.tabView = TabView(self)
        self.fileManager = FileManager(self)
        self.extensionList = ExtensionList(self)
        self.git = Git(self)
        self.search = GlobalSearch(self)
        self.sidebar = Sidebar(self)
        self.menubar = Menubar(self)
        self.terminal = Terminal(self)
        self.logs = Logs(self)

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

        self.setWindowTitle("Cipher")
        self.setWindowIcon(QIcon(f"{localAppData}/icons/window.png"))
        self.setStyleSheet(open(styles).read())

        sys.path.insert(0, f"{localAppData}/include")
        sys.path.insert(0, f"{localAppData}/site-packages")

        self.tabView.setupTabs()

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
            mod = import_module(f"extension.{path.name}")
            ext = mod.run(window=self)
        except EventTypeError:
            return
        except Exception as e:
            logging.error(f"Failed to add Extension - {e.__class__.__name__}: {e}")
            name = f"{name} (Disabled)"
            return self.extensionList.addItem(ExtensionItem(name, icon, settings))
        if not isinstance(ext, Extension):
            return

        item = ExtensionItem(name, icon, settings, True)
        self.extensionList.addItem(item)

        def onExtReady():
            item.setText(name)
            onReady = ext.__events__.get("onReady", [])
            for func in ext.__events__.get("onWorkspaceChanged", []):
                self.fileManager.onWorkspaceChanged.connect(lambda path: func(path))
            for func in ext.__events__.get("widgetChanged", []):
                self.tabView.currentChanged.connect(
                    lambda: func(self.currentFolder, self.currentFile)
                )
            for func in ext.__events__.get("onTabOpened", []):
                self.tabView.tabOpened.connect(lambda editor: func(editor))
            for func in ext.__events__.get("onSave", []):
                self.fileManager.onSave.connect(lambda: func(self.currentFile))
            for func in ext.__events__.get("onClose", []):
                self.onClose.connect(func)
            for func in onReady:
                func(self.currentFolder, self.currentFile)

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

    def closeEvent(self, _: QCloseEvent) -> None:
        self.logs.close()
        super().closeEvent(_)
        self.onClose.emit()

    def setWindowIcon(self, icon: QIcon) -> None:
        self.logs.setWindowIcon(icon)
        return super().setWindowIcon(icon)

    def setStyleSheet(self, styleSheet: str) -> None:
        self.logs.setStyleSheet(styleSheet)
        return super().setStyleSheet(styleSheet)

    def log(self, text: str, level=logging.ERROR):
        self.logs.log(text, level)

    def showMessage(self, msg: str) -> None:
        self.systemTray.showMessage("Cipher", msg=msg, msecs=30_000)
