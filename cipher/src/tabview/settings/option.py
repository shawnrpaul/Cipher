from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QContextMenuEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)


class BaseOption(QFrame):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setLayout(QVBoxLayout(self))

    @property
    def layout(self) -> QVBoxLayout:
        return super().layout()


class Option(BaseOption):
    def __init__(self, parent: QWidget, name: str) -> None:
        super().__init__(parent)
        self.nameWidget = QLabel(name)
        self.layout.addWidget(self.nameWidget)


class CheckBoxOption(BaseOption):
    updated = pyqtSignal(str, bool)

    def __init__(self, parent: QWidget, name: str, enabled: bool) -> None:
        super().__init__(parent)
        checkBox = QCheckBox(name, self)
        checkBox.setChecked(enabled)
        checkBox.stateChanged.connect(
            lambda state: self.updated.emit(name, bool(state))
        )
        self.layout.addWidget(checkBox)


class ListWidget(QListWidget):
    itemAdded = pyqtSignal(QListWidgetItem)
    itemUpdated = pyqtSignal(str, str)
    itemRemoved = pyqtSignal(QListWidgetItem)

    def __init__(self, parent: ListOption) -> None:
        super().__init__(parent)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if not self.indexAt(e.pos()).data():
            self.clearSelection()
        return super().mousePressEvent(e)

    def contextMenuEvent(self, a0: QContextMenuEvent) -> None:
        menu = QMenu(self)
        menu.addAction("Add").triggered.connect(self.createItem)
        menu.addSeparator()

        edit = menu.addAction("Edit")
        edit.triggered.connect(self.editItem)
        remove = menu.addAction("Remove")
        remove.triggered.connect(self.removeItem)

        if not self.selectedItem():
            edit.setEnabled(False)
            remove.setEnabled(False)
        menu.exec(self.viewport().mapToGlobal(a0.pos()))

    def selectedItem(self) -> None:
        items = self.selectedItems()
        if len(items) > 0:
            return items[0]

    def createItem(self) -> None:
        value, ok = QInputDialog.getText(
            self, "Add Item", "Give a value", QLineEdit.EchoMode.Normal, ""
        )
        if not value or not ok:
            return
        item = QListWidgetItem(value)
        self.addItem(value)
        self.itemAdded.emit(item)

    def editItem(self) -> None:
        item = self.selectedItem()
        prevName = item.text()
        value, ok = QInputDialog.getText(
            self, "Update Item", "Give a value", QLineEdit.EchoMode.Normal, prevName
        )
        if not value or not ok:
            return
        item.setText(value)
        self.itemUpdated.emit(prevName, value)

    def removeItem(self) -> None:
        self.takeItem(self.row(self.selectedItem()))

    def takeItem(self, row: int) -> QListWidgetItem:
        item = super().takeItem(row)
        self.itemRemoved.emit(item)
        return item


class ListOption(Option):
    added = pyqtSignal(str, str)
    updated = pyqtSignal(str, str, str)
    removed = pyqtSignal(str, str)

    def __init__(self, parent: QWidget, name: str, options: list[str]) -> None:
        super().__init__(parent, name)
        listWidget = ListWidget(self)
        for option in options:
            listWidget.addItem(option)
        self.layout.addWidget(listWidget)

        listWidget.itemAdded.connect(lambda item: self.added.emit(name, item.text()))
        listWidget.itemUpdated.connect(lambda *values: self.updated.emit(name, *values))
        listWidget.itemRemoved.connect(
            lambda item: self.removed.emit(name, item.text())
        )
