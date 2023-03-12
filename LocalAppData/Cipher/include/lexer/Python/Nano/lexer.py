from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
import builtins
import inspect
import re


__all__ = ("Lexer",)


class PyLexer(QsciLexerCustom):
    def __init__(self, editor) -> None:
        super().__init__(editor)

        self.setDefaultFont(QFont("Consolas"))
        self.setDefaultColor(QColor("#FFFFFF"))
        self.setDefaultPaper(QColor("#1E1E1E"))

        self._brightcyan = ("and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", 
                            "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is",
                            "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield")
        self._magenta = ("True", "False", "None")
        self._builtin_classes = tuple((name for name, obj in vars(builtins).items() if inspect.isclass(obj)))

        self.DEFAULT = 0
        self.INT = 1
        self.STRING = 2
        self.CLASSDEF = 3
        self.FUNCDEF = 4
        self.COMMENT = 5
        self.BRIGHTCYAN = 6
        self.MAGENTA = 7

        self.setColor(QColor("#D4D4D4"), self.DEFAULT)
        self.setColor(QColor("#B5CEA8"), self.INT)
        self.setColor(QColor("#6FE234"), self.STRING)
        self.setColor(QColor("#4EC9B0"), self.CLASSDEF)
        self.setColor(QColor("#589FCF"), self.FUNCDEF)
        self.setColor(QColor("#6A9955"), self.COMMENT)
        self.setColor(QColor("#34E2C3"), self.BRIGHTCYAN)
        self.setColor(QColor("#AD7FA8"), self.MAGENTA)

        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginsForegroundColor(QColor("#FFFFFF"))
        editor.setCaretLineBackgroundColor(QColor("#2C2C2C"))
        editor.setCaretForegroundColor(QColor("#AAAAAA"))

    def language(self) -> str:
        return "PyLexer"

    def description(self, style: int) -> str:
        if style == self.INT:
            return "INT"
        if style == self.STRING:
            return "STRING"
        if style == self.CLASSDEF:
            return "CLASSDEF"
        if style == self.FUNCDEF:
            return "FUNCDEF"
        if style == self.COMMENT:
            return "COMMENT"
        if style == self.BRIGHTCYAN:
            return "BRIGHTCYAN"
        if style == self.MAGENTA:
            return "MAGENTA"
        return "DEFAULT"

    def styleText(self, _: int, _2: int) -> None:
        self.startStyling(0)

        tokenList = [
            (token, len(bytearray(token, "utf-8"))) 
            for token in re.compile(r"[*]\/|\/[*]|\s+|\w+|\W").findall(self.editor().text())
        ]

        string = (False, None)
        comment = False
        for token, tokenLength in tokenList:
            if string[0]:
                self.setStyling(tokenLength, self.STRING)
                if token == string[1]:
                    string = (False, None)
            elif comment:
                self.setStyling(tokenLength, self.COMMENT)
                if "\n" in token:
                    comment = False
            elif token == " ":
                self.setStyling(tokenLength, self.DEFAULT)
            elif token.isnumeric():
                self.setStyling(tokenLength, self.INT)
            elif token in ("'", '"'):
                self.setStyling(tokenLength, self.STRING)
                string = (True, token)
            elif token == "#":
                self.setStyling(tokenLength, self.COMMENT)
                comment = True
            elif token in self._builtin_classes:
                self.setStyling(tokenLength, self.CLASSDEF)
            elif token in self._brightcyan:
                self.setStyling(tokenLength, self.BRIGHTCYAN)
                if token == "class":
                    self.DEFAULT = self.CLASSDEF
                elif token == "def":
                    self.DEFAULT = self.FUNCDEF
            elif token in self._magenta:
                self.setStyling(tokenLength, self.MAGENTA)
            else:
                self.setStyling(tokenLength, self.DEFAULT)
                self.DEFAULT = 0