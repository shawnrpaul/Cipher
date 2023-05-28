from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QTreeView,
    QVBoxLayout,
)

from .thread import Thread

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Git", "GitItem")


class GitItem(QStandardItem):
    def __init__(self, path: str):
        super().__init__(path)
        self.path = path


class GitType(QStandardItem):
    def __init__(self, staged: bool = False) -> None:
        super().__init__("Staged" if staged else "Changes")
        self.setEditable(False)


class GitModel(QStandardItemModel):
    def __init__(self, parent: QTreeView, window: MainWindow) -> None:
        super().__init__(parent)
        self.setObjectName("GitModel")
        self._window = window
        self._treeView = parent
        self._window.fileManager.onWorkspaceChanged.connect(self.status)
        self._window.fileManager.folderCreated.connect(lambda _: self.status())
        self._window.fileManager.fileCreated.connect(lambda _: self.status())
        self._window.fileManager.onSave.connect(self.status)

    def init(self) -> None:
        if (
            not self._window.currentFolder
            or Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        Thread(self, self.__gitinit).start()

    def __gitinit(self) -> None:
        subprocess.run(
            ["git", "init"], cwd=self._window.currentFolder, creationflags=0x08000000
        )
        self.__status()

    def __clone(self, url: str, username: str, password: str) -> None:
        subprocess.run(
            ["git" "clone" "--recursive", str(url)],
            cwd=self._window.currentFolder,
            input=f"{username}\n{password}\n".encode(),
            creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def clone(self) -> None:
        username, password = self._window.settings.get(
            "username"
        ), self._window.settings.get("password")
        if (
            not username
            or not password
            or not self._window.currentFolder
            or Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        url, ok = QInputDialog.getText(
            self._window, "Clone", "Give a url", QLineEdit.EchoMode.Normal, ""
        )
        if not url or not ok:
            return
        Thread(self, self.__clone, url, username, password).start()

    def __status(self) -> None:
        run = subprocess.run(
            ["git", "status", "-s"],
            cwd=self._window.currentFolder,
            stdout=subprocess.PIPE,
            creationflags=0x08000000,
        )
        self.clear()
        changes, staged = [], []
        for out in sorted(run.stdout.decode("utf-8").split("\n"))[1:]:
            if (index := out.find("->")) > -1:
                staged.append(GitItem(out[3:index]))
                out = out[index + 3 :]
                staged.append(GitItem(out))
                continue
            if out[1] in ("M", "D", "?"):
                changes.append(GitItem(out[3:]))
            if out[0] in ("M", "A", "D", "R"):
                staged.append(GitItem(out[3:]))

        if staged:
            _staged = GitType(staged=True)
            _staged.appendRows(staged)
            self.appendRow(_staged)
        if changes:
            _changes = GitType()
            _changes.appendRows(changes)
            self.appendRow(_changes)

    def status(self) -> None:
        if not Path(f"{self._window.currentFolder}\\.git").exists():
            self.clear()
            return
        thread = Thread(self, self.__status)
        thread.start()

    def __add(self, path: str) -> None:
        subprocess.run(
            f"git add {path}",
            cwd=self._window.currentFolder,
            creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def add(self, path: Optional[QModelIndex] = None) -> None:
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        if not path:
            path, ok = QInputDialog.getText(
                self._window,
                "Add",
                "Give the relative path",
                QLineEdit.EchoMode.Normal,
                "",
            )
            if not path or not ok:
                return
        else:
            item = self.itemFromIndex(path)
            path = item.path
        Thread(self, self.__add, path).start()

    def __remove(self, path: str) -> None:
        subprocess.run(
            ["git", "restore", "--staged", str(path)],
            cwd=self._window.currentFolder,
            creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def remove(self, path: Optional[QModelIndex] = None) -> None:
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        if not path:
            path, ok = QInputDialog.getText(
                self._window,
                "Remove",
                "Give the relative path",
                QLineEdit.EchoMode.Normal,
                "",
            )
            if not path or not ok:
                return
        else:
            item = self.itemFromIndex(path)
            path = item.path
        Thread(self, self.__remove, path).start()

    def __commit(self, message: str) -> None:
        subprocess.run(
            ["git", "commit", "-m", str(message)],
            cwd=self._window.currentFolder,
            # creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def commit(self):
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return

        message, ok = QInputDialog.getText(
            self._window,
            "Commit",
            "Provide a commit message",
            QLineEdit.EchoMode.Normal,
            "",
        )
        if not message or not ok:
            return
        Thread(self, self.__commit, message).start()

    def __push(self, username: str, password: str) -> None:
        subprocess.run(
            ["git", "push"],
            cwd=self._window.currentFolder,
            input=f"{username}\n{password}\n".encode(),
            creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def push(self) -> None:
        username, password = self._window.settings.get(
            "username"
        ), self._window.settings.get("password")
        if (
            not username
            or not password
            or not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        Thread(self, self.__push, username, password).start()

    def __pull(self, username: str, password: str) -> None:
        subprocess.run(
            "git pull",
            cwd=self._window.currentFolder,
            input=f"{username}\n{password}\n".encode(),
            creationflags=0x08000000,
            shell=True,
        )
        self.__status()

    def pull(self) -> None:
        username, password = self._window.settings.get(
            "username"
        ), self._window.settings.get("password")
        if (
            not username
            or not password
            or not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        Thread(self, self.__pull, username, password).start()


class GitView(QTreeView):
    def __init__(self, parent: QFrame, window: MainWindow, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._window = window
        self.setObjectName("GitView")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHeaderHidden(True)

        self.__gitModel = GitModel(self, window)
        self.__gitModel.rowsInserted.connect(self.expandAll)
        self.__gitModel.columnsInserted.connect(self.expandAll)
        self.setModel(self.__gitModel)

        self.createContextMenu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.menu.exec(self.viewport().mapToGlobal(pos))
        )

    def createContextMenu(self):
        self.menu = QMenu(self._window)
        self.menu.setObjectName("GitContextMenu")
        add = self.menu.addAction("Add")
        add.triggered.connect(self.add)
        remove = self.menu.addAction("Remove")
        remove.triggered.connect(self.remove)

    def init(self) -> None:
        self.__gitModel.init()

    def clone(self) -> None:
        self.__gitModel.clone()

    def status(self) -> None:
        self.__gitModel.status()

    def add(self) -> None:
        indexes = self.selectedIndexes()
        self.__gitModel.add(indexes[0] if indexes else None)

    def remove(self) -> None:
        indexes = self.selectedIndexes()
        self.__gitModel.remove(indexes[0] if indexes else None)

    def commit(self) -> None:
        self.__gitModel.commit()

    def push(self) -> None:
        self.__gitModel.push()

    def pull(self) -> None:
        self.__gitModel.pull()


class Git(QFrame):
    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.setObjectName("Git")
        self._window = window
        self.setLineWidth(1)
        self.setMaximumWidth(self.screen().size().width() // 2)
        self.setMinimumWidth(0)
        self.setBaseSize(100, 0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.gitView = GitView(self, window)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.gitView)

        self.setLayout(layout)
