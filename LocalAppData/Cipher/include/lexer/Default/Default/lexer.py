from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont


class DefaultLexer(QsciLexerCustom):
    def __init__(self, editor) -> None:
        super().__init__(editor)

        self.setDefaultFont(QFont("Consolas"))
        self.setDefaultColor(QColor("#FFFFFF"))
        self.setDefaultPaper(QColor("#1E1E1E"))

        self.DEFAULT = 0

        self.setColor(QColor("#D4D4D4"), self.DEFAULT)
        self.setPaper(QColor("#1E1E1E"), self.DEFAULT)

        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginsForegroundColor(QColor("#FFFFFF"))
        editor.setCaretLineBackgroundColor(QColor("#2C2C2C"))
        editor.setCaretForegroundColor(QColor("#AAAAAA"))

    def language(self) -> str:
        return "DefaultLexer"

    def description(self, _: int) -> str:
        return "DEFAULT"

    def styleText(self, start: int, _: int) -> None:
        self.startStyling(start)
        self.setStyling(len(self.editor().text()), self.DEFAULT)