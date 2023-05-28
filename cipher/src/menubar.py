from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, List

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar

from .thread import Thread

if TYPE_CHECKING:
    from .editor import Editor
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
        self.createFileMenu()
        self.createEditMenu()
        self.createGitMenu()
        self.createViewMenu()

    def createFileMenu(self) -> None:
        """Create the file menu box"""
        fileMenu = self.addMenu("File")
        self._menus.append(fileMenu)

        saveFile = fileMenu.addAction("Save File")
        saveFile.setShortcut("Ctrl+S")
        saveFile.triggered.connect(
            lambda: self._window.currentFile.saveFile()
            if self._window.currentFile
            else ...
        )

        saveAs = fileMenu.addAction("Save File As")
        saveAs.setShortcut("Ctrl+Shift+S")
        saveAs.triggered.connect(
            lambda: self._window.currentFile.saveAs()
            if self._window.currentFile
            else ...
        )

        fileMenu.addSeparator()

        newFile = fileMenu.addAction("New File")
        newFile.setShortcut("Ctrl+N")
        newFile.triggered.connect(self._window.fileManager.createFile)

        newFolder = fileMenu.addAction("New Folder")
        newFolder.setShortcut("Ctrl+Shift+N")
        newFolder.triggered.connect(self._window.fileManager.createFolder)

        fileMenu.addSeparator()

        openFile = fileMenu.addAction("Open File")
        openFile.setShortcut("Ctrl+O")
        openFile.triggered.connect(self._window.fileManager.openFile)

        openFile = fileMenu.addAction("Open File Path")
        openFile.setShortcut("Ctrl+Shift+P")
        openFile.triggered.connect(self._window.fileManager.openFilePath)

        reopen = fileMenu.addAction("Reopen Closed Tab")
        reopen.setShortcut("Ctrl+Shift+T")
        reopen.triggered.connect(self._window.tabView.reopenTab)

        openFolder = fileMenu.addAction("Open Folder")
        openFolder.setShortcut("Ctrl+Shift+O")
        openFolder.triggered.connect(self._window.fileManager.openFolder)

        closeFolder = fileMenu.addAction("Close Folder")
        closeFolder.setShortcut("Ctrl+K")
        closeFolder.triggered.connect(self._window.fileManager.closeFolder)

    def createEditMenu(self) -> None:
        """Creates the edit menu box"""
        editMenu = self.addMenu("Edit")
        self._menus.append(editMenu)

        copy = editMenu.addAction("Copy")
        copy.setShortcut("Ctrl+C")
        copy.triggered.connect(
            lambda: self._window.currentFile.copy() if self._window.currentFile else ...
        )

        cut = editMenu.addAction("Cut")
        cut.setShortcut("Ctrl+X")
        cut.triggered.connect(
            lambda: self._window.currentFile.cut() if self._window.currentFile else ...
        )

        paste = editMenu.addAction("Paste")
        paste.setShortcut("Ctrl+V")
        paste.triggered.connect(
            lambda: self._window.currentFile.paste()
            if self._window.currentFile
            else ...
        )

        find = editMenu.addAction("Find")
        find.setShortcut("Ctrl+F")
        find.triggered.connect(
            lambda: self._window.currentFile.find() if self._window.currentFile else ...
        )
        editMenu.addSeparator()

        styles = editMenu.addAction("Styles")
        styles.triggered.connect(
            lambda: self._window.tabView.setEditorTab(
                Path(f"{self._window.localAppData}\\styles\\styles.qss")
            )
        )

        shortcut = editMenu.addAction("Shortcuts")
        shortcut.triggered.connect(
            lambda: self._window.tabView.setEditorTab(
                Path(f"{self._window.localAppData}\\shortcuts.json")
            )
        )

        globalSettings = editMenu.addAction("Global Settings")
        globalSettings.triggered.connect(self.editGlobalSettings)

        workspaceSettings = editMenu.addAction("Workspace Settings")
        workspaceSettings.triggered.connect(self.editWorkspaceSettings)

        editTerminalSettings = editMenu.addAction("Terminal Settings")
        editTerminalSettings.triggered.connect(self.editTerminalSettings)

    def editGlobalSettings(self) -> None:
        """Opens the global settings as a tab to edit"""
        self._window.tabView.setEditorTab(
            Path(f"{self._window.localAppData}\\settings.json")
        )

    def editWorkspaceSettings(self) -> None:
        """Opens the workspace settings as a tab to edit.
        If a workspace isn't opened, the global settings will open instead"""
        if not self._window.currentFolder:
            return self.editGlobalSettings()
        self._window.tabView.setEditorTab(
            Path(f"{self._window.currentFolder}\\.Cipher\\settings.json")
        )

    def editTerminalSettings(self) -> None:
        """Opens the terminal settings to edit"""
        path = (
            Path(f"{self._window.currentFolder}\\.Cipher\\terminal.json")
            if self._window.currentFolder
            else Path(f"{self._window.localAppData}\\terminal.json")
        )
        self._window.tabView.setEditorTab(path)

    def createGitMenu(self) -> None:
        """Creates the git menu box"""
        git = self.addMenu("Git")
        self._menus.append(git)

        init = git.addAction("Init")
        init.triggered.connect(self._window.git.gitView.init)

        clone = git.addAction("Clone")
        clone.triggered.connect(self._window.git.gitView.clone)

        status = git.addAction("Status")
        status.triggered.connect(self._window.git.gitView.status)

        git.addSeparator()

        add = git.addAction("Add")
        add.triggered.connect(self._window.git.gitView.add)

        remove = git.addAction("Remove")
        remove.triggered.connect(self._window.git.gitView.remove)

        git.addSeparator()

        commit = git.addAction("Commit")
        commit.triggered.connect(self._window.git.gitView.commit)

        push = git.addAction("Push")
        push.triggered.connect(self._window.git.gitView.push)

        pull = git.addAction("Pull")
        pull.triggered.connect(self._window.git.gitView.pull)

    def createViewMenu(self) -> None:
        """Creates the view menu box"""
        view = self.addMenu("View")
        self._menus.append(view)

        run = view.addAction("Run")
        run.setShortcut("Ctrl+Shift+R")
        run.triggered.connect(self.run)

        terminal = view.addAction("Terminal")
        terminal.setShortcut("Ctrl+T")
        terminal.triggered.connect(self.terminal)

        explorer = view.addAction("Explorer")
        explorer.setShortcut("Ctrl+B")
        explorer.triggered.connect(self.explorer)

        close = view.addAction("Close Editor")
        close.setShortcut("Ctrl+W")
        close.triggered.connect(self._window.tabView.closeCurrentTab)

    def __run(self, path: Path, cmds: str, editor: Editor) -> None:
        """Runs the terminal commands

        Parameters
        ----------
        path : :class:`pathlib.Path`
            The path to open the terminal in. Uses the workspace path or the folder of the current path
        cmds : :class:`str`
            The command to run
        editor : Editor
            The current tab that will be run in the terminal
        """
        relativePath = editor.path.relative_to(path)
        subprocess.run(
            f'start /d "{path}" cmd /k "{cmds} {relativePath} & echo. & pause & exit"',
            shell=True,
        )

    def run(self) -> None:
        """Starts the thread to run the command"""
        if not self._window.currentFile:
            return
        currentFolder = (
            self._window.currentFolder
            if self._window.currentFolder
            else self._window.currentFile.path.parent
        )
        terminalSettings = (
            f"{self._window.currentFolder}\\.Cipher\\terminal.json"
            if self._window.currentFolder
            else f"{self._window.localAppData}\\terminal.json"
        )
        with open(terminalSettings) as f:
            data = json.load(f)
        cmds = data.get(self._window.currentFile.path.suffix)
        if not cmds:
            return
        Thread(self, self.__run, currentFolder, cmds, self._window.currentFile).start()

    def terminal(self) -> None:
        """Starts the terminal"""
        powershell = f"{os.getenv('AppData')}\\Microsoft\\Windows\\Start Menu\\Programs\\Windows PowerShell\\Windows PowerShell.lnk"
        currentFolder = self._window.currentFolder
        if not currentFolder:
            currentFolder = os.getenv("UserProfile")
        subprocess.run(f'start /d "{currentFolder}" "{powershell}"', shell=True)

    def explorer(self) -> None:
        """Opens or closes the :class:`sidebar.Explorer`"""
        widget = self._window._hsplit.widget(0)
        widget.setVisible(not widget.isVisible())
