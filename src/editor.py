from __future__ import annotations
from PyQt6.QtCore import QRect, QThread
from PyQt6.Qsci import QsciAPIs, QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QDropEvent, QFont
from PyQt6.QtWidgets import QCheckBox, QDialog, QLabel, QLineEdit, QPushButton
from importlib import util
from pathlib import Path
from typing import Dict, List, Tuple, TYPE_CHECKING, Union
import json

if TYPE_CHECKING:
    from .window import MainWindow

__all__ = ("Editor",)


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
    def __init__(self, window: MainWindow, path: Path = None) -> None:
        super().__init__()
        self.setObjectName(path.name)
        self.path = path
        self.setUtf8(True)
        self.zoomOut(2)
        self.releaseShortcut(self.grabShortcut("Ctrl+Tab"))

        self.cursorPositionChanged.connect(self._cursorPositionChanged)

        self.setCaretLineVisible(True)
        self.setCaretWidth(2)

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

        styles = getStyling(window.localAppData)
        self._lexer, self.autoCompleter = None, None
        for data in styles.values():
            if path.suffix in data.get("extensions", ()):
                _path = Path(data.get("location", ".\\")).absolute()
                if not _path.exists():
                    break
                self._lexer, self.api = loadLexerAndApi(self, _path)
                if not data.get("autocomplete"):
                    break
                _path = Path(data.get("autocomplete", ".\\")).absolute()
                if not _path.exists():
                    break
                workspace = window.fileManager.getWorkspaceSettings()
                self.autoCompleter = loadAutoCompleter(_path, self.api, path, workspace)
                break

        if not self._lexer:
            self._lexer, self.api = loadLexerAndApi(
                self, f"{window.localAppData}\\include\\lexer\\Default"
            )

        self.setLexer(self._lexer)

        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, 30)
        self.setMarginsFont(QFont("Consolas"))
        self._fileDropped = window.fileDropped

    def dropEvent(self, e: QDropEvent) -> None:
        self._fileDropped(e)
        return super().dropEvent(e)

    def _cursorPositionChanged(self, line: int, index: int) -> None:
        if not self.autoCompleter:
            return
        self.autoCompleter.setPos(line + 1, index, self.text())
        self.autoCompleter.start()

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


def loadLexerAndApi(editor: Editor, path: str) -> Tuple[QsciLexerCustom, QsciAPIs]:
    spec = util.spec_from_file_location("lexer", f"{(path)}\\lexer.py")
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lexer = mod.lexer(editor)
    return lexer, QsciAPIs(lexer)


def loadAutoCompleter(path: str, *args, **kwargs) -> QThread:
    spec = util.spec_from_file_location("autocomplete", f"{(path)}\\autocomplete.py")
    lexer = util.module_from_spec(spec)
    spec.loader.exec_module(lexer)
    return lexer.autocomplete(*args, **kwargs)


def getStyling(localAppData: str) -> Dict[str, Dict[Union[str, List[str]]]]:
    with open(f"{localAppData}\\styles\\syntax.json") as f:
        return json.load(f)
