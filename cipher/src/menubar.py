from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar, QFileDialog, QMenu

if TYPE_CHECKING:
    from .window import Window

__all__ = ("Menubar",)


class Menubar(QMenuBar):
    """The window menubar

    Parameters
    ----------
    window: :class:`Window`
        The window
    """

    def __init__(self, window: Window) -> None:
        super().__init__()
        self.setObjectName("Menubar")
        self._window = window
        self._menus: List[QAction] = []
        self.createFileMenu()
        self.createEditMenu()
        self.createViewMenu()

        self.window.shortcut.fileChanged.connect(self.updateShortcuts)
        self.updateShortcuts()

    @property
    def window(self) -> Window:
        return self._window

    def addMenu(self, name: str) -> QMenu:
        menu = super().addMenu(name)
        self._menus.append(menu)
        return menu

    def createFileMenu(self) -> None:
        """Create the file menu box"""
        fileMenu = self.addMenu("File")

        saveFile = fileMenu.addAction("Save File")
        saveFile.triggered.connect(
            lambda: self._window.currentFile.saveFile()
            if self._window.currentFile
            else ...
        )

        saveAs = fileMenu.addAction("Save File As")
        saveAs.triggered.connect(
            lambda: self._window.currentFile.saveAs()
            if self._window.currentFile
            else ...
        )

        fileMenu.addSeparator()

        newFile = fileMenu.addAction("New File")
        newFile.triggered.connect(self._window.fileManager.createFile)

        newFolder = fileMenu.addAction("New Folder")
        newFolder.triggered.connect(self._window.fileManager.createFolder)

        fileMenu.addSeparator()

        openFile = fileMenu.addAction("Open File")
        openFile.triggered.connect(self._window.fileManager.openFile)

        openFile = fileMenu.addAction("Open File Path")
        openFile.triggered.connect(self._window.fileManager.openFilePath)

        reopen = fileMenu.addAction("Reopen Closed Tab")
        reopen.triggered.connect(self._window.tabView.reopenTab)

        openFolder = fileMenu.addAction("Open Folder")
        openFolder.triggered.connect(self._window.fileManager.openFolder)

        openFolderTreeView = fileMenu.addAction("Open Folder in Tree View")
        openFolderTreeView.triggered.connect(self.openFolderTreeView)

        closeFolder = fileMenu.addAction("Close Folder")
        closeFolder.triggered.connect(self._window.fileManager.closeFolder)

    def openFolderTreeView(self) -> None:
        if not self._window.currentFolder:
            return
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a Folder", "C:/", options=QFileDialog().options()
        )
        if not folder:
            return
        self._window.fileSplitter.addFileManager(Path(folder))

    def createEditMenu(self) -> None:
        """Creates the edit menu box"""
        editMenu = self.addMenu("Edit")

        copy = editMenu.addAction("Copy")
        copy.triggered.connect(
            lambda: self._window.currentFile.copy() if self._window.currentFile else ...
        )

        cut = editMenu.addAction("Cut")
        cut.triggered.connect(
            lambda: self._window.currentFile.cut() if self._window.currentFile else ...
        )

        paste = editMenu.addAction("Paste")
        paste.triggered.connect(
            lambda: self._window.currentFile.paste()
            if self._window.currentFile
            else ...
        )

        find = editMenu.addAction("Find")
        find.triggered.connect(
            lambda: self._window.currentFile.find() if self._window.currentFile else ...
        )
        editMenu.addSeparator()

        styles = editMenu.addAction("Styles")
        styles.triggered.connect(
            lambda: self._window.tabView.createTab(
                Path(f"{self._window.localAppData}/styles/styles.qss")
            )
        )

        shortcut = editMenu.addAction("Shortcuts")
        shortcut.triggered.connect(
            lambda: self._window.tabView.createTab(
                Path(f"{self._window.localAppData}/shortcuts.json")
            )
        )

        globalSettings = editMenu.addAction("Global Settings")
        globalSettings.triggered.connect(self.editGlobalSettings)

        workspaceSettings = editMenu.addAction("Workspace Settings")
        workspaceSettings.triggered.connect(self.editWorkspaceSettings)

        editRunFile = editMenu.addAction("Run Settings")
        editRunFile.triggered.connect(self.editRunFile)

    def editGlobalSettings(self) -> None:
        """Opens the global settings as a tab to edit"""
        self._window.tabView.createTab(
            Path(f"{self._window.localAppData}/settings.json")
        )

    def editWorkspaceSettings(self) -> None:
        """Opens the workspace settings as a tab to edit.
        If a workspace isn't opened, the global settings will open instead"""
        if not self._window.currentFolder:
            return self.editGlobalSettings()
        self._window.tabView.createTab(
            Path(f"{self._window.currentFolder}/.cipher/settings.json")
        )

    def editRunFile(self) -> None:
        """Opens the run.bat or run.sh to edit"""
        if not self._window.currentFolder:
            return
        if sys.platform == "win32":
            path = Path(f"{self._window.currentFolder}/.cipher/run.bat")
        else:
            path = Path(f"{self._window.currentFolder}/.cipher/run.sh")
        self._window.tabView.createTab(path)

    def createViewMenu(self) -> None:
        """Creates the view menu box"""
        view = self.addMenu("View")

        view.addAction("Fullscreen").triggered.connect(
            lambda: self.window.showFullScreen()
            if not self.window.isFullScreen()
            else self.window.showMaximized()
        )
        view.addAction("Explorer").triggered.connect(self.explorer)
        view.addAction("Terminal").triggered.connect(self.terminal)
        view.addAction("Logs").triggered.connect(self.logs)
        view.addAction("Run").triggered.connect(self.run)
        view.addAction("Close Editor").triggered.connect(
            self._window.tabView.closeCurrentTab
        )

    def explorer(self) -> None:
        """Opens or closes the :class:`sidebar.Explorer`"""
        widget = self._window.hsplit.widget(0)
        visible = not widget.isVisible()
        widget.setVisible(visible)
        widget.setFocus() if visible else ...

    def terminal(self) -> None:
        outputView = self.window.outputView
        if (
            not outputView.isHidden()
            and outputView.currentWidget() == self.window.terminal
        ):
            return outputView.hide()
        outputView.show()
        outputView.setCurrentWidget(self.window.terminal)

    def logs(self) -> None:
        outputView = self.window.outputView
        if not outputView.isHidden() and outputView.currentWidget() == self.window.logs:
            return outputView.hide()
        outputView.show()
        outputView.setCurrentWidget(self.window.logs)

    def run(self) -> None:
        if self.window.outputView.isHidden():
            self.window.outputView.show()
        self.window.terminal.run()

    def updateShortcuts(self) -> None:
        """Updates the shortcuts when `shortcuts.json` updates"""
        with open(f"{self.window.localAppData}/shortcuts.json") as f:
            shortcuts = json.load(f)
        for menu in self._menus:
            for action in menu.actions():
                if not (name := action.text()):
                    continue
                action.setShortcut(shortcuts.get(name, ""))
