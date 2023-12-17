from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Union

from PyQt6.QtCore import Qt
from PyQt6.Qsci import QsciAPIs, QsciLexer, QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QDropEvent, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import QFileDialog

from .tab import Tab
from .search import Search

if TYPE_CHECKING:
    from .window import Window

__all__ = ("Editor",)


class Editor(QsciScintilla, Tab):
    """The text editor

    Parameters
    ----------
    window: `Window`
        The window object
    path: `Path`
        The path of the file being edited

    Attributes
    ----------
    path: `Path`
        The path of the file being edited
    """

    def __init__(self, window: Window, path: Path) -> None:
        super().__init__(window=window, path=path)
        self.setObjectName(path.name)
        self._watcher.fileChanged.connect(self.updateText)
        self.setUtf8(True)
        self.zoomOut(2)

        self.setCaretLineVisible(True)
        self.setCaretWidth(2)

        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)
        self.setCallTipsStyle(QsciScintilla.CallTipsStyle.CallTipsContext)

        self.setAnnotationDisplay(QsciScintilla.AnnotationDisplay.AnnotationBoxed)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)
        self.setEolMode(QsciScintilla.EolMode.EolUnix)
        self.setEolVisibility(False)

        styles = self.getEditorStyles()
        localAppData = f"{window.localAppData}/include"
        lexer = None
        if info := styles.get(path.suffix):
            language, folder = info.get("language"), info.get("lexer")
            lexerPath = Path(
                f"{localAppData}/lexer/{language}/{folder}/run.py"
            ).absolute()
            if lexerPath.exists():
                lexer = self.loadLexer(language, folder)

        if not lexer:
            lexer = self.loadLexer("Default", "Default")

        self.setLexer(lexer)

        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, 30)

        self.commands = self.standardCommands()
        self.setShortcutKeys()
        self._window.shortcut.fileChanged.connect(self.setShortcutKeys)

    @property
    def lexer(self) -> QsciLexerCustom:
        """Overrides the lexer to return the current lexer

        Returns
        -------
        :class:`QsciLexerCustom`
            The custom lexer used per language
        """
        return self._lexer

    @property
    def api(self) -> QsciAPIs:
        return self._api

    def dropEvent(self, e: QDropEvent) -> None:
        """Overrides the :meth:`dropEvent` to open a tab if a file was dropped

        Parameters
        ----------
        e : QDropEvent
            The drop event
        """
        urls = e.mimeData().urls()
        if urls and (path := urls[0]).isLocalFile():
            self._window.tabView.createTab(Path(path.toLocalFile()))
            return

        return super().dropEvent(e)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if self.selectedText():
            selection = list(self.getSelection())
            if e.key() == Qt.Key.Key_QuoteDbl:
                self.insertAt('"', selection[0], selection[1])
                self.insertAt('"', selection[2], selection[3] + 1)
                selection[1] += 1
                selection[3] += 1
                return self.setSelection(*selection)
            elif e.key() == Qt.Key.Key_Apostrophe:
                self.insertAt("'", selection[0], selection[1])
                self.insertAt("'", selection[2], selection[3] + 1)
                selection[1] += 1
                selection[3] += 1
                return self.setSelection(*selection)
            elif e.key() == Qt.Key.Key_ParenLeft:
                self.insertAt("(", selection[0], selection[1])
                self.insertAt(")", selection[2], selection[3] + 1)
                selection[1] += 1
                selection[3] += 1
                return self.setSelection(*selection)
            elif e.key() == Qt.Key.Key_BracketLeft:
                self.insertAt("[", selection[0], selection[1])
                self.insertAt("]", selection[2], selection[3] + 1)
                selection[1] += 1
                selection[3] += 1
                return self.setSelection(*selection)
            elif e.key() == Qt.Key.Key_BraceLeft:
                self.insertAt("{", selection[0], selection[1])
                self.insertAt("}", selection[2], selection[3] + 1)
                selection[1] += 1
                selection[3] += 1
                return self.setSelection(*selection)
            elif e.key() == Qt.Key.Key_Tab and selection[0] == selection[2]:
                tabWidth = self.tabWidth()
                self.insertAt(" " * tabWidth, selection[0], 0)
                selection[1] = selection[3] + tabWidth
                selection[3] = 0
                return self.setSelection(*selection)
        return super().keyPressEvent(e)

    def updateText(self) -> None:
        """Updates the text. Triggers when :attr:`watcher` detects a change."""
        if not self.path.exists():
            return
        cursor = self.getCursorPosition()
        self.setText(self.path.read_text("utf-8"))
        self.setCursorPosition(*cursor)

    def setShortcutKeys(self) -> None:
        with open(f"{self._window.localAppData}/shortcuts.json") as f:
            shortcuts = json.load(f)
        for command in self.commands.commands():
            command = command.command()
            name, key = command.name, 0
            if sequence := shortcuts.get(name):
                keySequence = QKeySequence.fromString(sequence)
                key = keySequence[0]
                for i in range(1, keySequence.count()):
                    key |= keySequence[i]
                key = key.toCombined()
            self.commands.find(command).setKey(key)

    def saveFile(self) -> None:
        """Saves the editor"""
        self._watcher.removePath(str(self.path))
        self.path.write_text(self.text(), encoding="utf-8")
        self._watcher.addPath(str(self.path))
        self._window.fileManager.onSave.emit(self)

    def saveAs(self) -> None:
        """Saves the editor as a new file"""
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save as",
            str(self._window.currentFolder) if self._window.currentFolder else "C:/",
            "All Files (*);;Python files (*.py);;JSON files (*.json)",
        )
        if not file:
            return
        self._watcher.removePath(str(self.path))
        self.path = Path(file)
        self.path.write_text(self.text(), "utf-8")
        self._watcher.addPath(str(self.path))
        self._window.tabView.setTabText(
            self._window.tabView.currentIndex(), self.path.name
        )
        self._window.fileManager.onSave.emit(self)

    def copy(self) -> None:
        """Copies the selected text. If no text is selected, the line will copied"""
        if not self.hasSelectedText():
            return self.SendScintilla(self.SCI_LINECOPY)
        return super().copy()

    def cut(self) -> None:
        """Cuts the selected text. If no text is selected, the line will cut"""
        if not self.hasSelectedText():
            return self.SendScintilla(self.SCI_LINECUT)
        return super().cut()

    def find(self) -> None:
        """Starts the editor search"""
        Search(self).exec()

    def search(self, string: str, cs: bool = False, forward: bool = True) -> None:
        """Seaches for string in the editor

        Parameters
        ----------
        string : `str`
            The string to search for
        cs : `bool`
            Case sensitive, by default False
        forward : `bool`
            Check ahead for behind the cursor, by default True
        """
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
            return self._highlight(len(string), pos)
        pos = self._search(string, cs, forward, 0, len(self.text()))
        if pos >= 0:
            return self._highlight(len(string), pos)
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
        """Sets search for the string"""
        search = self.SendScintilla
        search(self.SCI_SETTARGETSTART, start if forward else end)
        search(self.SCI_SETTARGETEND, end if forward else start)
        search(self.SCI_SETSEARCHFLAGS, self.SCFIND_MATCHCASE if cs else 0)
        return search(self.SCI_SEARCHINTARGET, len(string), bytes(string, "utf-8"))

    def _highlight(self, length: int, pos: int) -> None:
        """Highlights the seached text if found

        Parameters
        ----------
        length: `int`
            The string being
        pos: `int`
            The starting position of the highlight
        """
        self.SendScintilla(self.SCI_SETSEL, pos, pos + length)

    def loadLexer(self, language: str, lexerFolder: str) -> QsciLexerCustom:
        """Loads the lexer and api

        Parameters
        ----------
        language: `str`
            The language of the lexer
        lexerFolder: `str`
            The lexer name

        Returns
        -------
        QsciLexerCustom
            The lexer
        """
        path = f"lexer.{language}.{lexerFolder}.run"
        try:
            mod = import_module(path)
            lexer = mod.run(self)
            return lexer
        except Exception as e:
            return None

    def setLexer(self, lexer: QsciLexer | None = None) -> None:
        self._lexer = lexer
        self._api = QsciAPIs(lexer) if lexer else None
        return super().setLexer(lexer)

    def getEditorStyles(self) -> Dict[str, Dict[Union[str, List[str]]]]:
        """Returns the editor styles"""
        with open(f"{self._window.localAppData}/styles/lexer.json") as f:
            return json.load(f)
