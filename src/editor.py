from .lexer import DefaultLexer, JSONLexer, PyLexer
from PyQt6.QtCore import QRect
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QCheckBox, QDialog, QLabel, QLineEdit, QPushButton
from pathlib import Path

__all__ = ("Editor",)


class Search(QDialog):
    def __init__(self, editor: "Editor") -> None:
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

        self.label = QLabel(self)
        self.label.setObjectName("Label")
        self.label.setGeometry(QRect(10, 10, 91, 16))
        self.label.setText("Give Text to Find")

        self.setWindowTitle("Find")
        self.textBox.setText(editor.selectedText())


class Editor(QsciScintilla):
    def __init__(self, path: Path, styles=None) -> None:
        super().__init__()
        self.setObjectName(path.name)
        self.path = path.absolute()
        self.setUtf8(True)
        self.zoomOut(2)

        self.setCaretForegroundColor(QColor("#AAAAAA"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#2C2C2C"))

        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)
        self.setEolMode(QsciScintilla.EolMode.EolUnix)
        self.setEolVisibility(False)

        if path.name.endswith(".py"):
            self.pylexer = PyLexer(styles=styles)
        elif path.name.endswith(".json"):
            self.pylexer = JSONLexer(styles=styles)
        else:
            self.pylexer = DefaultLexer(styles=styles)
        self.setLexer(self.pylexer)

        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, 30)
        self.setMarginsForegroundColor(QColor("#FFFFFF"))
        self.setMarginsBackgroundColor(QColor("#1E1E1E"))
        self.setMarginsFont(QFont("Consolas"))

    def find(self) -> None:
        Search(self).exec()

    def search(self, string: str, cs: bool = False, forward: bool = True) -> None:
        if not string:
            return
        if self.hasSelectedText():
            pos = self.getSelection()[2:] if forward else self.getSelection()[:2]
        else:
            pos = self.getCursorPosition()
        start = self.positionFromLineIndex(*pos) if forward else 0
        end = len(self.text()) if forward else self.positionFromLineIndex(*pos)
        pos = self._search(string, cs, forward, start, end)
        if pos >= 0:
            return self._highlight(string, pos)
        pos = self._search(string, cs, forward, 0, len(self.text()))
        if pos >= 0:
            return self._highlight(string, pos)
        if self.hasSelectedText():
            pos = self.getSelection()[2:] if forward else self.getSelection()[:2]
            return self.setCursorPosition(*pos)

    def _search(
        self,
        string: str,
        cs: bool = False,
        forward: bool = True,
        start: int = -1,
        end: int = -1,
    ) -> None:
        search = self.SendScintilla
        search(self.SCI_SETTARGETSTART, start if forward else end)
        search(self.SCI_SETTARGETEND, end if forward else start)
        search(self.SCI_SETSEARCHFLAGS, self.SCFIND_MATCHCASE if cs else 0)
        return search(self.SCI_SEARCHINTARGET, len(string), bytes(string, "utf-8"))

    def _highlight(self, string: str, pos: int) -> None:
        search = self.SendScintilla
        search(self.SCI_SETSEL, pos, pos + len(string))
