from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QCheckBox, QDialog, QLabel, QLineEdit, QPushButton

if TYPE_CHECKING:
    from cipher import Editor

__all__ = ("Find",)


class Find(QDialog):
    def __init__(self, editor: Editor) -> None:
        super().__init__(editor)
        self.setObjectName("Find")
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
