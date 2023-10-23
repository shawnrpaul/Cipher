from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, List

from PyQt6.QtCore import QModelIndex, QRect, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
)

from .thread import Thread

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

    from .tab import Editor
    from .window import MainWindow

__all__ = ("Search", "GlobalSearch")


class Search(QDialog):
    def __init__(self, editor: Editor) -> None:
        super().__init__()
        self.setObjectName("Search")
        self.textBox = QLineEdit(self)
        self.textBox.setObjectName("Textbox")
        self.textBox.setGeometry(QRect(10, 30, 251, 21))
        self.textBox.setPlaceholderText(editor.selectedText())

        self.cs = QCheckBox(self)
        self.cs.setObjectName("Case")
        self.cs.setGeometry(QRect(10, 70, 41, 17))
        self.cs.setText("Aa")

        self.next = QPushButton(self)
        self.next.setObjectName("Next")
        self.next.setGeometry(QRect(190, 70, 71, 23))
        self.next.setText("Next")
        self.next.clicked.connect(
            lambda: editor.search(
                self.textBox.text(),
                self.cs.isChecked(),
                forward=True,
            )
        )

        self.previous = QPushButton(self)
        self.previous.setObjectName("Previous")
        self.previous.setText("Previous")
        self.previous.setGeometry(QRect(110, 70, 75, 23))
        self.previous.clicked.connect(
            lambda: editor.search(
                self.textBox.text(),
                self.cs.isChecked(),
                forward=False,
            )
        )

        self.label = QLabel(self)
        self.label.setObjectName("Label")
        self.label.setGeometry(QRect(10, 10, 91, 16))
        self.label.setText("Give Text to Find")

        self.setWindowTitle("Find")
        self.textBox.setText(editor.selectedText())


class GlobalSearchFile(QStandardItem):
    def __init__(self, file: str):
        super().__init__(file)

        self.setEditable(False)


class GlobalSearchMatch(QStandardItem):
    def __init__(self, text: str, path: Path, index: int, cs: re._FlagsType):
        super().__init__(text)
        self.path = path
        self._index = index
        self.cs = cs

        self.setEditable(False)


class GlobalSearchModel(QStandardItemModel):
    def __init__(self, parent, window: MainWindow):
        super().__init__(parent)
        self.rootNode = self.invisibleRootItem()
        self._window = window

    @property
    def window(self) -> MainWindow:
        return self._window

    def isBinary(self, path: Path) -> None:
        with open(path, "rb") as f:
            return b"\0" in f.read(1024)

    def recursiveSearch(
        self,
        folder: Path,
        currentFolder: Path,
        text: str,
        cs: re._FlagsType,
        pattern: List[str],
        excluded: List[str],
    ):
        for dirEntry in os.scandir(folder):
            if dirEntry.name in excluded:
                continue
            path = Path(dirEntry.path)
            if path.is_file():
                if pattern and path.suffix not in pattern:
                    continue
                editor = self._window.tabView.getTab(path)
                try:
                    found = tuple(
                        (
                            GlobalSearchMatch(match.group(), path, i, cs)
                            for i, match in enumerate(
                                re.compile(rf"{text}", cs).finditer(
                                    path.read_text("utf-8")
                                    if not editor
                                    else editor.text()
                                )
                            )
                        )
                    )
                    if not found:
                        continue
                    file = GlobalSearchFile(str(path.relative_to(currentFolder)))
                    file.appendRows(found)
                    self.appendRow(file)
                except Exception as e:
                    (e.__class__, e)
                    continue
            elif path.is_dir():
                self.recursiveSearch(path, currentFolder, text, cs, pattern, excluded)

    def search(
        self,
        currentFolder: Path,
        text: str,
        case: bool,
        pattern: List[str],
        excluded: List[str],
    ):
        self.clear()

        if not text or not currentFolder:
            return

        cs = re.IGNORECASE if not case else 0

        for dirEntry in os.scandir(currentFolder):
            if dirEntry.name in excluded:
                continue
            path = Path(dirEntry.path)
            if path.is_file():
                if pattern and path.suffix not in pattern:
                    continue
                editor = self._window.tabView.getTab(path)
                try:
                    found = tuple(
                        (
                            GlobalSearchMatch(match.group(), path, i)
                            for i, match in enumerate(
                                re.compile(rf"{text}", cs).finditer(
                                    path.read_text("utf-8")
                                    if not editor
                                    else editor.text()
                                )
                            )
                        )
                    )
                    if not found:
                        continue
                    file = GlobalSearchFile(str(path.relative_to(currentFolder)))
                    file.appendRows(found)
                    self.appendRow(file)
                except Exception:
                    continue
            elif path.is_dir():
                self.recursiveSearch(path, currentFolder, text, cs, pattern, excluded)


class GlobalSearchView(QTreeView):
    def __init__(self, parent: QWidget, window: MainWindow, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._window = window
        self.setObjectName("SearchView")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHeaderHidden(True)

        self.__searchModel = GlobalSearchModel(self, window)
        self.setModel(self.__searchModel)

        self.clicked.connect(self.view)

    def view(self, index: QModelIndex):
        item = self.__searchModel.itemFromIndex(index)
        if isinstance(item, GlobalSearchMatch):
            if not (editor := self._window.tabView.getTab(item.path)):
                editor = self._window.tabView.createTab(item.path)
            for i, match in enumerate(
                re.compile(rf"{item.text()}", item.cs).finditer(editor.text())
            ):
                if i == item._index:
                    start = editor.lineIndexFromPosition(match.start())
                    end = editor.lineIndexFromPosition(match.end())
                    return editor.setSelection(*start, *end)
        if self.isExpanded(index):
            return self.collapse(index)
        return self.expand(index)

    def search(self, text: str, case: bool = False):
        currentFolder = self._window.currentFolder
        pattern = self._window.settings["search-pattern"]
        exclude = self._window.settings["search-exclude"]
        thread = Thread(
            self, self.__searchModel.search, currentFolder, text, case, pattern, exclude
        )
        thread.finished.connect(self.expandAll)
        thread.start()


class GlobalSearch(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.setLineWidth(1)
        self.setMaximumWidth(self.screen().size().width() // 2)
        self.setMinimumWidth(0)
        self.setBaseSize(100, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.textBox = QLineEdit(self)
        self.textBox.setObjectName("TextBox")

        self.cs = QCheckBox(self)
        self.cs.setObjectName("Case")
        self.cs.setText("Aa")

        self.searchView = GlobalSearchView(self, window)
        self.textBox.returnPressed.connect(
            lambda: self.searchView.search(self.textBox.text(), self.cs.isChecked())
        )
        self.textBox.textChanged.connect(
            lambda: self.searchView.search("", False)
            if not self.textBox.text()
            else ...
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.textBox)
        layout.addWidget(self.cs)
        layout.addWidget(self.searchView)

        self.setLayout(layout)
