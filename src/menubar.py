from __future__ import annotations
from typing import TYPE_CHECKING

from .thread import Thread
from PyQt6.QtWidgets import QMenuBar

from pathlib import Path
import json
import os

if TYPE_CHECKING:
    from .window import MainWindow
    from .editor import Editor

__all__ = ("Menubar",)


class Menubar(QMenuBar):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window
        self.setObjectName("Menubar")
        self.createFileMenu()
        self.createEditMenu()
        self.createView()
        self.__threads = []

    def createFileMenu(self) -> None:
        fileMenu = self.addMenu("File")

        saveFile = fileMenu.addAction("Save File")
        saveFile.setShortcut("Ctrl+S")
        saveFile.triggered.connect(self._window.saveFile)

        saveAs = fileMenu.addAction("Save File As")
        saveAs.setShortcut("Ctrl+Shift+S")
        saveAs.triggered.connect(self._window.saveAs)

        fileMenu.addSeparator()

        newFile = fileMenu.addAction("New File")
        newFile.setShortcut("Ctrl+N")
        newFile.triggered.connect(self._window.createFile)

        newFolder = fileMenu.addAction("New Folder")
        newFolder.setShortcut("Ctrl+Shift+N")
        newFolder.triggered.connect(self._window.createFolder)

        fileMenu.addSeparator()

        openFile = fileMenu.addAction("Open File")
        openFile.setShortcut("Ctrl+O")
        openFile.triggered.connect(self._window.openFile)

        openFile = fileMenu.addAction("Open File Path")
        openFile.setShortcut("Ctrl+Shift+P")
        openFile.triggered.connect(self._window.openFilePath)

        reopen = fileMenu.addAction("Reopen Closed Tab")
        reopen.setShortcut("Ctrl+Shift+T")
        reopen.triggered.connect(self._window.tabView.reopenTab)

        openFolder = fileMenu.addAction("Open Folder")
        openFolder.setShortcut("Ctrl+Shift+O")
        openFolder.triggered.connect(self._window.openFolder)

        openFolder = fileMenu.addAction("Close Folder")
        openFolder.setShortcut("Ctrl+K")
        openFolder.triggered.connect(self._window.closeFolder)

    def createEditMenu(self) -> None:
        editMenu = self.addMenu("Edit")

        copy = editMenu.addAction("Copy")
        copy.setShortcut("Ctrl+C")
        copy.triggered.connect(self._window.copy)

        cut = editMenu.addAction("Cut")
        cut.setShortcut("Ctrl+X")
        cut.triggered.connect(self._window.cut)

        paste = editMenu.addAction("Paste")
        paste.setShortcut("Ctrl+V")
        paste.triggered.connect(self._window.paste)

        find = editMenu.addAction("Find")
        find.setShortcut("Ctrl+F")
        find.triggered.connect(self._window.find)

        editMenu.addSeparator()

        globalSettings = editMenu.addAction("Global Settings")
        globalSettings.triggered.connect(self._window.sidebar.settingsMousePressEvent)

        workspaceSettings = editMenu.addAction("Workspace Settings")
        workspaceSettings.triggered.connect(self.editWorkspaceSettings)

        editTerminalSettings = editMenu.addAction("Terminal Settings")
        editTerminalSettings.triggered.connect(self.editTerminalSettings)

    def editWorkspaceSettings(self) -> None:
        if not self._window.currentFolder:
            return self._window.sidebar.settingsMousePressEvent()
        self._window.setEditorTab(
            Path(f"{self._window.currentFolder}\\.Cipher\\settings.json")
        )

    def editTerminalSettings(self) -> None:
        path = (
            Path(f"{self._window.currentFolder}\\.Cipher\\terminal.json")
            if self._window.currentFolder
            else Path(f"{self._window.localAppData}\\terminal.json")
        )
        self._window.setEditorTab(path)

    def createView(self):
        view = self.addMenu("View")

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
        _path = editor.path.relative_to(path)
        os.system(f'start /d "{path}" cmd /k "{cmds} {_path} & echo. & pause & exit"')

    def run(self) -> None:
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
        thread = Thread(self.__run, currentFolder, cmds, self._window.currentFile)
        thread.finished.connect(lambda: self.__threads.remove(thread))
        self.__threads.append(thread)
        thread.start()

    def terminal(self) -> None:
        powershell = f"{os.getenv('AppData')}\\Microsoft\\Windows\\Start Menu\\Programs\\Windows PowerShell\\Windows PowerShell.lnk"
        currentFolder = self._window.currentFolder
        if not currentFolder:
            currentFolder = os.getenv("UserProfile")
        os.system(f'start /d "{currentFolder}" "{powershell}"')

    def explorer(self) -> None:
        widget = self._window.hsplit.widget(0)
        widget.setVisible(not widget.isVisible())
