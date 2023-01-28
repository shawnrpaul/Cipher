from __future__ import annotations
from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from typing import Dict, TYPE_CHECKING
import json
import re

if TYPE_CHECKING:
    from editor import Editor


class JSONLexer(QsciLexerCustom):
    def __init__(self, editor: Editor) -> None:
        super().__init__(editor)

        styles = getStyling()

        self.setDefaultFont(QFont(styles.get("font")))
        self.setDefaultColor(QColor(styles.get("tabs")))
        self.setDefaultPaper(QColor(styles.get("paper")))

        self.DEFAULT = 0
        self.STRING = 2
        self.BOOL = 3
        self.BRACKETS = 4

        self.setColor(QColor(styles.get("default")), self.DEFAULT)
        self.setColor(QColor(styles.get("string")), self.STRING)
        self.setColor(QColor(styles.get("brackets")), self.BRACKETS)
        self.setColor(QColor(styles.get("bool")), self.BOOL)

        self.setPaper(QColor(styles.get("paper")), self.DEFAULT)
        self.setPaper(QColor(styles.get("paper")), self.STRING)
        self.setPaper(QColor(styles.get("paper")), self.BRACKETS)
        self.setPaper(QColor(styles.get("paper")), self.BOOL)

        editor = self.parent()
        editor.setMarginsBackgroundColor(QColor(styles.get("paper")))
        editor.setMarginsForegroundColor(QColor(styles.get("margin")))
        editor.setCaretLineBackgroundColor(QColor(styles.get("caretBackground")))
        editor.setCaretForegroundColor(QColor(styles.get("caretForeground")))

    def language(self) -> str:
        return "JSONLexer"

    def description(self, style: int) -> str:
        if style == self.STRING:
            return "STRING"
        if style == self.BOOL:
            return "BOOL"
        if style == self.BRACKETS:
            return "BRACKETS"
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

        string = False
        for token, tokenLength in tokenList:
            if string:
                self.setStyling(tokenLength, self.STRING)
                if token in '"':
                    string = False
            elif token in ("true", "false", "null"):
                self.setStyling(tokenLength, self.BOOL)
            elif token in '"':
                self.setStyling(tokenLength, self.STRING)
                string = True
            elif token in "{}[]":
                self.setStyling(tokenLength, self.BRACKETS)
            else:
                self.setStyling(tokenLength, self.DEFAULT)


def getStyling() -> Dict[str, str]:
    with open(f"{str(Path(__file__).absolute().parent)}\\syntax.json") as f:
        return json.load(f)


def lexer(*args, **kwargs) -> JSONLexer:
    return JSONLexer(*args, **kwargs)
