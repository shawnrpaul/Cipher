from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
import re


class JSONLexer(QsciLexerCustom):
    def __init__(self, editor) -> None:
        super().__init__(editor)

        self.setDefaultFont(QFont("Consolas"))
        self.setDefaultColor(QColor("#FFFFFF"))
        self.setDefaultPaper(QColor("#1E1E1E"))

        self.DEFAULT = 0
        self.NUM = 1
        self.STRING = 2
        self.BOOL = 3
        self.BRACKETS = 4

        self.setColor(QColor("#D4D4D4"), self.DEFAULT)
        self.setColor(QColor("#B5CEA8"), self.NUM)
        self.setColor(QColor("#CE9178"), self.STRING)
        self.setColor(QColor("#C586C0"), self.BRACKETS)
        self.setColor(QColor("#6796E6"), self.BOOL)

        editor = self.parent()
        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginsForegroundColor(QColor("#FFFFFF"))
        editor.setCaretLineBackgroundColor(QColor("#2C2C2C"))
        editor.setCaretForegroundColor(QColor("#AAAAAA"))

    def language(self) -> str:
        return "JSONLexer"

    def description(self, style: int) -> str:
        if style == self.NUM:
            return "NUM"
        if style == self.STRING:
            return "STRING"
        if style == self.BOOL:
            return "BOOL"
        if style == self.BRACKETS:
            return "BRACKETS"
        return "DEFAULT"

    def styleText(self, _: int, __: int) -> None:
        editor = self.editor()
        self.startStyling(0)

        text = editor.text()

        p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")
        tokenList = [
            (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)
        ]

        string = False
        for token, tokenLength in tokenList:
            if string:
                self.setStyling(tokenLength, self.STRING)
                if token in '"':
                    string = False
            elif token.isnumeric():
                self.setStyling(tokenLength, self.NUM)
            elif token in ("true", "false", "null"):
                self.setStyling(tokenLength, self.BOOL)
            elif token in '"':
                self.setStyling(tokenLength, self.STRING)
                string = True
            elif token in "{}[]":
                self.setStyling(tokenLength, self.BRACKETS)
            else:
                self.setStyling(tokenLength, self.DEFAULT)