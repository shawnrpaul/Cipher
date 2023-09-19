from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar, QFileDialog

from .thread import Thread

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Menubar",)


class Menubar(QMenuBar):
    """The window menubar

    Parameters
    ----------
    window: :class:`MainWindow`
        The window
    """

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Menubar")
        self._window = window
        self._menus: List[QAction] = []
        with open(f"{window.localAppData}/shortcuts.json") as f:
            shortcuts = json.load(f)
        self.createFileMenu(shortcuts)
        self.createEditMenu(shortcuts)
        self.createViewMenu(shortcuts)
        self.createGitMenu()

    def createFileMenu(self, shortcuts: dict[str, str]) -> None:
        """Create the file menu box"""
        fileMenu = self.addMenu("File")
        self._menus.append(fileMenu)

        saveFile = fileMenu.addAction("Save File")
        saveFile.setShortcut(shortcuts.get("Save File", ""))
        saveFile.triggered.connect(
            lambda: self._window.currentFile.saveFile()
            if self._window.currentFile
            else ...
        )

        saveAs = fileMenu.addAction("Save File As")
        saveAs.setShortcut(shortcuts.get("Save File As", ""))
        saveAs.triggered.connect(
            lambda: self._window.currentFile.saveAs()
            if self._window.currentFile
            else ...
        )

        fileMenu.addSeparator()

        newFile = fileMenu.addAction("New File")
        newFile.setShortcut(shortcuts.get("New File", ""))
        newFile.triggered.connect(self._window.fileManager.createFile)

        newFolder = fileMenu.addAction("New Folder")
        newFolder.setShortcut(shortcuts.get("New Folder", ""))
        newFolder.triggered.connect(self._window.fileManager.createFolder)

        fileMenu.addSeparator()

        openFile = fileMenu.addAction("Open File")
        openFile.setShortcut(shortcuts.get("Open File", ""))
        openFile.triggered.connect(self._window.fileManager.openFile)

        openFile = fileMenu.addAction("Open File Path")
        openFile.setShortcut(shortcuts.get("Open File Path", ""))
        openFile.triggered.connect(self._window.fileManager.openFilePath)

        reopen = fileMenu.addAction("Reopen Closed Tab")
        reopen.setShortcut(shortcuts.get("Reopen Closed Tab", ""))
        reopen.triggered.connect(self._window.tabView.reopenTab)

        openFolder = fileMenu.addAction("Open Folder")
        openFolder.setShortcut(shortcuts.get("Open Folder", ""))
        openFolder.triggered.connect(self._window.fileManager.openFolder)

        openFolderTreeView = fileMenu.addAction("Open Folder in Tree View")
        openFolderTreeView.setShortcut(shortcuts.get("Open Folder in Tree View", ""))
        openFolderTreeView.triggered.connect(self.openFolderTreeView)

        closeFolder = fileMenu.addAction("Close Folder")
        closeFolder.setShortcut(shortcuts.get("Close Folder", ""))
        closeFolder.triggered.connect(self._window.fileManager.closeFolder)

    def openFolderTreeView(self) -> None:
        if not self._window.currentFolder:
            return
        folder = QFileDialog.getExistingDirectory(
            self, "Pick a Folder", "C:/", options=QFileDialog().options()
        )
        if not folder:
            return
        self._window._vsplit.addFileManager(Path(folder))

    def createEditMenu(self, shortcuts: dict[str, str]) -> None:
        """Creates the edit menu box"""
        editMenu = self.addMenu("Edit")
        self._menus.append(editMenu)

        copy = editMenu.addAction("Copy")
        copy.setShortcut(shortcuts.get("Copy", ""))
        copy.triggered.connect(
            lambda: self._window.currentFile.copy() if self._window.currentFile else ...
        )

        cut = editMenu.addAction("Cut")
        cut.setShortcut(shortcuts.get("Cut", ""))
        cut.triggered.connect(
            lambda: self._window.currentFile.cut() if self._window.currentFile else ...
        )

        paste = editMenu.addAction("Paste")
        paste.setShortcut(shortcuts.get("Paste", ""))
        paste.triggered.connect(
            lambda: self._window.currentFile.paste()
            if self._window.currentFile
            else ...
        )

        find = editMenu.addAction("Find")
        find.setShortcut(shortcuts.get("Find", ""))
        find.triggered.connect(
            lambda: self._window.currentFile.find() if self._window.currentFile else ...
        )
        editMenu.addSeparator()

        styles = editMenu.addAction("Styles")
        styles.setShortcut(shortcuts.get("Styles", ""))
        styles.triggered.connect(
            lambda: self._window.tabView.createTab(
                Path(f"{self._window.localAppData}/styles/styles.qss")
            )
        )

        shortcut = editMenu.addAction("Shortcuts")
        shortcut.setShortcut(shortcuts.get("Shortcuts", ""))
        shortcut.triggered.connect(
            lambda: self._window.tabView.createTab(
                Path(f"{self._window.localAppData}/shortcuts.json")
            )
        )

        globalSettings = editMenu.addAction("Global Settings")
        globalSettings.setShortcut(shortcuts.get("Global Settings", ""))
        globalSettings.triggered.connect(self.editGlobalSettings)

        workspaceSettings = editMenu.addAction("Workspace Settings")
        workspaceSettings.setShortcut(shortcuts.get("Workspace Settings", ""))
        workspaceSettings.triggered.connect(self.editWorkspaceSettings)

        # if sys.platform == "win32":
        # editRunFile = editMenu.addAction("Run Settings")
        # editRunFile.setShortcut(shortcuts.get("Run Settings", ""))
        # editRunFile.triggered.connect(self.editRunFile)

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
        """Opens the run.bat to edit"""
        if not self._window.currentFolder:
            return
        path = Path(f"{self._window.currentFolder}/.cipher/run.bat")
        self._window.tabView.createTab(path)

    def createViewMenu(self, shortcuts: dict[str, str]) -> None:
        """Creates the view menu box"""
        view = self.addMenu("View")
        self._menus.append(view)

        # if sys.platform == "win32":
        # run = view.addAction("Run")
        # run.setShortcut(shortcuts.get("Run", ""))
        # run.triggered.connect(self.run)

        # terminal = view.addAction("Terminal")
        # terminal.setShortcut(shortcuts.get("Terminal", ""))
        # terminal.triggered.connect(self.terminal)

        explorer = view.addAction("Explorer")
        explorer.setShortcut(shortcuts.get("Explorer", ""))
        explorer.triggered.connect(self.explorer)

        close = view.addAction("Close Editor")
        close.setShortcut(shortcuts.get("Close Editor", ""))
        close.triggered.connect(self._window.tabView.closeCurrentTab)

    def run(self) -> None:
        """Starts the thread to run the command"""
        if not self._window.currentFolder:
            return
        path = Path(f"{self._window.currentFolder}/.cipher/run.bat")
        path.write_text("@echo off\n") if not path.exists() else ...
        powershell = f"{os.getenv('AppData')}/Microsoft/Windows/Start Menu/Programs/Windows PowerShell/Windows PowerShell.lnk"
        subprocess.run(
            [
                "start",
                "/d",
                str(self._window.currentFolder),
                powershell,
                f"{self._window.currentFolder}/.cipher/run.bat",
            ],
            shell=True,
        )

    def terminal(self) -> None:
        """Starts the terminal"""
        powershell = f"{os.getenv('AppData')}/Microsoft/Windows/Start Menu/Programs/Windows PowerShell/Windows PowerShell.lnk"
        currentFolder = self._window.currentFolder
        if not currentFolder:
            currentFolder = os.getenv("UserProfile")
        subprocess.run(f'start /d "{currentFolder}" "{powershell}"', shell=True)

    def explorer(self) -> None:
        """Opens or closes the :class:`sidebar.Explorer`"""
        widget = self._window._hsplit.widget(0)
        widget.setVisible(not widget.isVisible())

    def createGitMenu(self) -> None:
        """Creates the git menu box"""
        git = self.addMenu("Git")
        self._menus.append(git)

        init = git.addAction("Init")
        init.triggered.connect(self._window.git.init)

        clone = git.addAction("Clone")
        clone.triggered.connect(self._window.git.clone)

        branch = git.addAction("Branch")
        branch.triggered.connect(self._window.git.branch)

        checkout = git.addAction("Checkout")
        checkout.triggered.connect(self._window.git.checkout)

        git.addSeparator()

        status = git.addAction("Status")
        status.triggered.connect(self._window.git.status)

        add = git.addAction("Add")
        add.triggered.connect(self._window.git.add)

        remove = git.addAction("Remove")
        remove.triggered.connect(self._window.git.remove)

        git.addSeparator()

        commit = git.addAction("Commit")
        commit.triggered.connect(self._window.git.commit)

        push = git.addAction("Push")
        push.triggered.connect(self._window.git.push)

        pull = git.addAction("Pull")
        pull.triggered.connect(self._window.git.pull)
