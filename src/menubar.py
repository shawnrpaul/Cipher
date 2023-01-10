from __future__ import annotations
from typing import Callable, TypeVar, TYPE_CHECKING
from PyQt6.QtWidgets import QMenuBar

if TYPE_CHECKING:
    from .window import MainWindow

T = TypeVar("T", bound=Callable[[], None])

__all__ = ("Menubar",)


class Menubar(QMenuBar):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self.setObjectName("Menubar")
        self.createFileMenu(window)
        self.createEditMenu(window)

    def createFileMenu(self, window: MainWindow):
        fileMenu = self.addMenu("File")

        saveFile = fileMenu.addAction("Save File")
        saveFile.setShortcut("Ctrl+S")
        saveFile.triggered.connect(window.saveFile)

        saveAs = fileMenu.addAction("Save File As")
        saveAs.setShortcut("Ctrl+Shift+S")
        saveAs.triggered.connect(window.saveAs)

        fileMenu.addSeparator()

        newFile = fileMenu.addAction("New File")
        newFile.setShortcut("Ctrl+N")
        newFile.triggered.connect(window.createFile)

        newFolder = fileMenu.addAction("New Folder")
        newFolder.setShortcut("Ctrl+Shift+N")
        newFolder.triggered.connect(window.createFolder)

        fileMenu.addSeparator()

        openFile = fileMenu.addAction("Open File")
        openFile.setShortcut("Ctrl+O")
        openFile.triggered.connect(window.openFile)

        openFile = fileMenu.addAction("Open File Path")
        openFile.setShortcut("Ctrl+Shift+P")
        openFile.triggered.connect(window.openFilePath)

        openFolder = fileMenu.addAction("Open Folder")
        openFolder.setShortcut("Ctrl+Shift+O")
        openFolder.triggered.connect(window.openFolder)

        openFolder = fileMenu.addAction("Close Folder")
        openFolder.setShortcut("Ctrl+K")
        openFolder.triggered.connect(window.closeFolder)

    def createEditMenu(self, window: MainWindow) -> None:
        editMenu = self.addMenu("Edit")

        copy = editMenu.addAction("Copy")
        copy.setShortcut("Ctrl+C")
        copy.triggered.connect(window.copy)

        cut = editMenu.addAction("Cut")
        cut.setShortcut("Ctrl+X")
        cut.triggered.connect(window.cut)

        paste = editMenu.addAction("Paste")
        paste.setShortcut("Ctrl+V")
        paste.triggered.connect(window.paste)

        editMenu.addSeparator()

        find = editMenu.addAction("Find")
        find.setShortcut("Ctrl+F")
        find.triggered.connect(window.find)
