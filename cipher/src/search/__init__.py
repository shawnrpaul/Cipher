from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt6.QtWidgets import QCheckBox, QFrame, QLineEdit, QSizePolicy, QVBoxLayout
from .view import SearchView

if TYPE_CHECKING:
    from cipher import Window

__all__ = ("Search",)


class Search(QFrame):
    def __init__(self, window: Window) -> None:
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

        self.searchView = SearchView(self, window)
        self.textBox.returnPressed.connect(
            lambda: self.searchView.search(self.textBox.text(), self.cs.isChecked())
        )
        self.textBox.textChanged.connect(
            lambda: (
                self.searchView.search("", False) if not self.textBox.text() else ...
            )
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.textBox)
        layout.addWidget(self.cs)
        layout.addWidget(self.searchView)

        self.setLayout(layout)

    def focus(self) -> None:
        self.textBox.selectAll()
        self.textBox.setFocus()
