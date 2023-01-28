from __future__ import annotations
from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from typing import Dict, TYPE_CHECKING
from keyword import kwlist
import builtins
import types
import inspect
import json
import re

if TYPE_CHECKING:
    from editor import Editor

__all__ = ("Lexer",)


class PyLexer(QsciLexerCustom):
    def __init__(self, editor: Editor) -> None:
        super().__init__(editor)

        styles = getStyling()

        self.setDefaultFont(QFont(styles.get("font")))
        self.setDefaultColor(QColor(styles.get("tabs")))
        self.setDefaultPaper(QColor(styles.get("paper")))

        self.BUILTINS_FUNCTIONS = []
        self.BUILTINS_CLASSES = []
        for name, obj in vars(builtins).items():
            if isinstance(obj, types.BuiltinFunctionType):
                self.BUILTINS_FUNCTIONS.append(name)
            elif inspect.isclass(obj):
                self.BUILTINS_CLASSES.append(name)

        self.DEFAULT = 0
        self.KEYWORD = 1
        self.TYPES = 2
        self.STRING = 3
        self.VARIABLE = 4
        self.BRACKETS = 5
        self.COMMENTS = 6
        self.FUNCTION = 7
        self.CLASS = 8

        self.setColor(QColor(styles.get("default")), self.DEFAULT)
        self.setColor(QColor(styles.get("keyword")), self.KEYWORD)
        self.setColor(QColor(styles.get("types")), self.TYPES)
        self.setColor(QColor(styles.get("string")), self.STRING)
        self.setColor(QColor(styles.get("variable")), self.VARIABLE)
        self.setColor(QColor(styles.get("brackets")), self.BRACKETS)
        self.setColor(QColor(styles.get("comments")), self.COMMENTS)
        self.setColor(QColor(styles.get("function")), self.FUNCTION)
        self.setColor(QColor(styles.get("class")), self.CLASS)

        self.setPaper(QColor(styles.get("paper")), self.DEFAULT)
        self.setPaper(QColor(styles.get("paper")), self.KEYWORD)
        self.setPaper(QColor(styles.get("paper")), self.TYPES)
        self.setPaper(QColor(styles.get("paper")), self.STRING)
        self.setPaper(QColor(styles.get("paper")), self.VARIABLE)
        self.setPaper(QColor(styles.get("paper")), self.BRACKETS)
        self.setPaper(QColor(styles.get("paper")), self.COMMENTS)
        self.setPaper(QColor(styles.get("paper")), self.FUNCTION)
        self.setPaper(QColor(styles.get("paper")), self.CLASS)

        editor = self.parent()
        editor.setMarginsBackgroundColor(QColor(styles.get("paper")))
        editor.setMarginsForegroundColor(QColor(styles.get("margin")))
        editor.setCaretLineBackgroundColor(QColor(styles.get("caretBackground")))
        editor.setCaretForegroundColor(QColor(styles.get("caretForeground")))

    def language(self) -> str:
        return "PyLexer"

    def description(self, style: int) -> str:
        if style == self.KEYWORD:
            return "KEYWORD"
        if style == self.TYPES:
            return "TYPES"
        if style == self.STRING:
            return "STRING"
        if style == self.VARIABLE:
            return "VARIABLE"
        if style == self.BRACKETS:
            return "BRACKETS"
        if style == self.COMMENTS:
            return "COMMENTS"
        if style == self.FUNCTION:
            return "FUNCTION"
        if style == self.CLASS:
            return "CLASS"
        return "DEFAULT"

    def styleText(self, start: int, end: int) -> None:
        editor = self.editor()
        start = 0
        end = len(editor.text())
        self.startStyling(start)

        text = editor.text()[start:end]

        p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")
        tokenList = [
            (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)
        ]

        string = (False, None)
        comment = False
        for token, tokenLength in tokenList:
            if string[0]:
                self.setStyling(tokenLength, self.STRING)
                if token == string[1]:
                    string = (False, None)
            elif comment:
                self.setStyling(tokenLength, self.COMMENTS)
                if "\n" in token:
                    comment = False
            elif (
                token in (" ", ".", "*", "/", "+", "-", ",", "=", ":")
                or token.isnumeric()
            ):
                self.setStyling(tokenLength, 0)
            elif token in ("from", "import", "(", ")", "[", "]", "{", "}"):
                self.setStyling(tokenLength, self.BRACKETS)
            elif token in kwlist:
                self.setStyling(tokenLength, self.KEYWORD)
                if token == "class":
                    self.DEFAULT = self.CLASS
                elif token == "def":
                    self.DEFAULT = self.FUNCTION
            elif token == "self":
                self.setStyling(tokenLength, self.VARIABLE)
            elif token in self.BUILTINS_FUNCTIONS:
                self.setStyling(tokenLength, self.FUNCTION)
            elif token in self.BUILTINS_CLASSES:
                self.setStyling(tokenLength, self.CLASS)
            elif token in ("'", '"'):
                self.setStyling(tokenLength, self.STRING)
                string = (True, token)
            elif token == "#":
                self.setStyling(tokenLength, self.COMMENTS)
                comment = True
            else:
                self.setStyling(tokenLength, self.DEFAULT)
                self.DEFAULT = 0


def getStyling() -> Dict[str, str]:
    with open(f"{str(Path(__file__).absolute().parent)}\\syntax.json") as f:
        return json.load(f)


def lexer(*args, **kwargs) -> PyLexer:
    return PyLexer(*args, **kwargs)
