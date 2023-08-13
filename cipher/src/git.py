from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QModelIndex, QProcess, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
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

    def displayError(self, title: str, msg: str) -> None:
        dialog = QMessageBox(self._window)
        dialog.setWindowTitle(title)
        dialog.setText(msg)
        dialog.exec()

    def init(self) -> None:
        if (
            not self._window.currentFolder
            or Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(self.status)
        self._window.onClose.connect(process.kill)
        process.start("git", ["init"])

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
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Clone", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["clone", "--recursive", url])
        process.write(f"{username}\n{password}\n".encode())

    def branch(self) -> None:
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        branch, ok = QInputDialog.getText(
            self._window, "Branch", "Create a new branch", QLineEdit.EchoMode.Normal, ""
        )
        if not branch or not ok:
            return
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Clone", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["checkout", "-b", str(branch)])

    def checkout(self) -> None:
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        run = subprocess.run(
            ["git", "branch"],
            cwd=self._window.currentFolder,
            stdout=subprocess.PIPE,
            creationflags=0x08000000,
        )
        branch, ok = QInputDialog.getText(
            self._window,
            "Checkout",
            f"Give a branch name\n{run.stdout.decode('utf-8')[:-1]}",
            QLineEdit.EchoMode.Normal,
            "",
        )
        if not branch or not ok:
            return
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Checkout", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else [
                self.status(),
                tuple((editor.updateText() for editor in self._window.tabView)),
            ]
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["checkout", branch])

    def __status(self, ouput: str) -> None:
        self.clear()
        changes, staged = [], []
        for out in sorted(ouput.split("\n"))[1:]:
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
            return self.clear()
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Restore", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.__status(process.readAllStandardOutput().data().decode())
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["status", "-s"])

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
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Restore", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["add", str(path)])

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
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Restore", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["restore", "--staged", str(path)])

    def commit(self):
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        message, ok = QInputDialog.getText(
            self._window,
            "Commit",
            "Enter your message",
            QLineEdit.EchoMode.Normal,
            "",
        )
        if not message or not ok:
            return
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Commit", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["commit", "-m", message])

    def reset(self) -> None:
        if (
            not self._window.currentFolder
            or not Path(f"{self._window.currentFolder}\\.git").exists()
        ):
            return
        parameters, ok = QInputDialog.getText(
            self._window,
            "Reset",
            "Enter the name of the file",
            QLineEdit.EchoMode.Normal,
            "",
        )
        if not parameters or not ok:
            return
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Reset", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["reset", parameters])

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
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Push", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["push"])
        process.write(f"{username}\n{password}\n".encode())

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
        process = QProcess(self)
        process.setWorkingDirectory(str(self._window.currentFolder))
        process.finished.connect(
            lambda: self.displayError(
                "Pull", process.readAllStandardError().data().decode()
            )
            if process.exitCode()
            else self.status()
        )
        self._window.onClose.connect(process.kill)
        process.start("git", ["pull"])


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

    def branch(self) -> None:
        self.__gitModel.branch()

    def checkout(self) -> None:
        self.__gitModel.checkout()

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

    def init(self) -> None:
        self.gitView.init()

    def branch(self) -> None:
        self.gitView.branch()

    def checkout(self) -> None:
        self.gitView.checkout()

    def clone(self) -> None:
        self.gitView.clone()

    def status(self) -> None:
        self.gitView.status()

    def add(self) -> None:
        self.gitView.add()

    def remove(self) -> None:
        self.gitView.remove()

    def commit(self) -> None:
        self.gitView.commit()

    def push(self) -> None:
        self.gitView.push()

    def pull(self) -> None:
        self.gitView.pull()
