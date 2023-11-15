from PyQt6.Qsci import QsciLexerPython
from PyQt6.QtGui import QColor, QFont


class PyLexer(QsciLexerPython):
    def __init__(self, editor) -> None:
        super().__init__(editor)

        self.setFont(QFont("Consolas"))
        self.setPaper(QColor("#1E1E1E"))
        self.setDefaultPaper(QColor("#1E1E1E"))
        self.setColor(QColor("#D4D4D4"))
        self.setDefaultColor(QColor("#D4D4D4"))

        self.setColor(QColor("#6796E6"), self.Keyword)
        self.setColor(QColor("#4EC9B0"), self.ClassName)
        self.setColor(QColor("#DCDCAA"), self.FunctionMethodName)
        self.setColor(QColor("#DCDCAA"), self.Decorator)
        self.setColor(QColor("#B5CEA8"), self.Number)
        self.setColor(QColor("#CE9178"), self.DoubleQuotedString)
        self.setColor(QColor("#CE9178"), self.SingleQuotedString)
        self.setColor(QColor("#CE9178"), self.TripleSingleQuotedString)
        self.setColor(QColor("#CE9178"), self.TripleDoubleQuotedString)
        self.setColor(QColor("#CE9178"), self.DoubleQuotedFString)
        self.setColor(QColor("#CE9178"), self.SingleQuotedFString)
        self.setColor(QColor("#CE9178"), self.TripleSingleQuotedFString)
        self.setColor(QColor("#CE9178"), self.TripleDoubleQuotedFString)
        self.setColor(QColor("#CE9178"), self.UnclosedString)
        self.setColor(QColor("#6A9955"), self.Comment)
        self.setColor(QColor("#6A9955"), self.CommentBlock)

        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginsForegroundColor(QColor("#FFFFFF"))
        editor.setCaretLineBackgroundColor(QColor("#2C2C2C"))
        editor.setCaretForegroundColor(QColor("#AAAAAA"))
