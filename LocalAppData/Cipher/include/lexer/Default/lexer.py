from __future__ import annotations
from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from pathlib import Path
from typing import Dict, TYPE_CHECKING
import json

if TYPE_CHECKING:
    from editor import Editor


class DefaultLexer(QsciLexerCustom):
    def __init__(self, editor: Editor) -> None:
        super().__init__(editor)

        styles = getStyling()

        self.setDefaultFont(QFont(styles.get("font")))
        self.setDefaultColor(QColor(styles.get("tabs")))
        self.setDefaultPaper(QColor(styles.get("paper")))

        self.DEFAULT = 0

        self.setColor(QColor(styles.get("color")), self.DEFAULT)
        self.setPaper(QColor(styles.get("paper")), self.DEFAULT)

        editor = self.parent()
        editor.setMarginsBackgroundColor(QColor(styles.get("paper")))
        editor.setMarginsForegroundColor(QColor(styles.get("margin")))
        editor.setCaretLineBackgroundColor(QColor(styles.get("caretBackground")))
        editor.setCaretForegroundColor(QColor(styles.get("caretForeground")))

    def language(self) -> str:
        return "DefaultLexer"

    def description(self, style: int) -> str:
        return "DEFAULT"

    def styleText(self, start: int, end: int) -> None:
        editor = self.editor()
        end = len(editor.text())

        self.startStyling(start)
        self.setStyling(end, self.DEFAULT)


def getStyling() -> Dict[str, str]:
    with open(f"{str(Path(__file__).absolute().parent)}\\syntax.json") as f:
        return json.load(f)


def lexer(*args, **kwargs) -> DefaultLexer:
    return DefaultLexer(*args, **kwargs)
