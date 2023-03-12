from __future__ import annotations
from typing import Dict, List, Tuple, TYPE_CHECKING, Union

from PyQt6.QtCore import QRect, Qt, QThread
from PyQt6.Qsci import QsciAPIs, QsciCommand, QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QDropEvent, QFont, QKeyEvent
from PyQt6.QtWidgets import QCheckBox, QDialog, QLabel, QLineEdit, QPushButton

from importlib import import_module
from pathlib import Path
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


class Editor(QsciScintilla):
    def __init__(self, window: MainWindow, path: Path = None) -> None:
        super().__init__()
        self.setObjectName(path.name)
        self.path = path
        self.setUtf8(True)
        self.zoomOut(2)
        self.releaseShortcut(self.grabShortcut("Ctrl+Tab"))

        self.setCaretLineVisible(True)
        self.setCaretWidth(2)

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

        styles = getEditorExtensions(window.localAppData)
        localAppData = f"{window.localAppData}\\include"
        self._lexer, self.autoCompleter = None, None
        for lang, data in styles.items():
            if path.suffix in data.get("extensions", ()):
                folder = data.get("lexer")
                _path = Path(
                    f"{localAppData}\\lexer\\{lang}\\{folder}\\run.py"
                ).absolute()
                if not _path.exists():
                    break
                self._lexer, self.api = loadLexerAndApi(self, lang, folder)
                if not self._lexer:
                    break
                folder = data.get("autocomplete")
                _path = Path(
                    f"{localAppData}\\autocomplete\\{lang}\\{folder}\\run.py"
                ).absolute()
                if not _path.exists():
                    break
                workspace = window.fileManager.getWorkspaceSettings()
                self.autoCompleter = loadAutoCompleter(
                    _path, lang, folder, self, self.api, path, workspace.get("project")
                )
                if self.autoCompleter:
                    self.setAutoCompletionSource(
                        QsciScintilla.AutoCompletionSource.AcsAPIs
                    )
                    self.cursorPositionChanged.connect(self.autoCompleter.start)
                break

        if not self._lexer:
            self._lexer, self.api = loadLexerAndApi(self, "Default", "Default")
        if not self.autoCompleter:
            self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)

        self.setLexer(self._lexer)

        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, 30)
        self.setMarginsFont(QFont("Consolas"))
        self._fileDropped = window.fileDropped

        self.commands = self.standardCommands()
        self.commands.find(QsciCommand.Command.LineCopy).setKey(0)
        self.commands.find(QsciCommand.Command.SelectionCopy).setKey(0)
        self.commands.find(QsciCommand.Command.LineCut).setKey(0)
        self.commands.find(QsciCommand.Command.SelectionCut).setKey(0)
        self.commands.find(QsciCommand.Command.LineTranspose).setKey(0)
        self.commands.find(QsciCommand.Command.MoveSelectedLinesDown).setKey(
            (Qt.KeyboardModifier.AltModifier | Qt.Key.Key_Down).toCombined()
        )
        self.commands.find(QsciCommand.Command.MoveSelectedLinesUp).setKey(
            (Qt.KeyboardModifier.AltModifier | Qt.Key.Key_Up).toCombined()
        )

    def dropEvent(self, e: QDropEvent) -> None:
        self._fileDropped(e)
        return super().dropEvent(e)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        selectedText = self.selectedText()
        if selectedText:
            selection = list(self.getSelection())
            if e.key() == Qt.Key.Key_Tab and selection[0] == selection[2]:
                tabWidth = self.tabWidth()
                self.insertAt(" " * tabWidth, selection[0], 0)
                selection[1] = selection[3] + tabWidth
                selection[3] = 0
                return self.setSelection(*selection)
        return super().keyPressEvent(e)

    def copy(self) -> None:
        if not self.hasSelectedText():
            return self.SendScintilla(self.SCI_LINECOPY)
        return super().copy()

    def cut(self) -> None:
        if not self.hasSelectedText():
            return self.SendScintilla(self.SCI_LINECUT)
        return super().cut()

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


def loadLexerAndApi(
    editor: Editor, lang: str, folder: str
) -> Tuple[QsciLexerCustom, QsciAPIs]:
    path = f"lexer.{lang}.{folder}.run"
    try:
        mod = import_module(path)
        lexer = mod.run(editor)
        return lexer, QsciAPIs(lexer)
    except Exception as e:
        return None, None


def loadAutoCompleter(path: Path, lang: str, folder: str, *args, **kwargs) -> QThread:
    path = f"autocomplete.{lang}.{folder}.run"
    try:
        mod = import_module(path)
        ac = mod.run(*args, **kwargs)
        return ac
    except Exception as e:
        return None


def getEditorExtensions(localAppData: str) -> Dict[str, Dict[Union[str, List[str]]]]:
    with open(f"{localAppData}\\styles\\syntax.json") as f:
        return json.load(f)
