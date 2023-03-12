from pygments.lexers.python import PythonLexer
from pygments.token import Token
from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont

PYGMENTS_DEFAULT = 0
PYGMENTS_COMMENT = 1
PYGMENTS_KEYWORD = 2
PYGMENTS_FUNCTION = 3
PYGMENTS_CLASS = 4
PYGMENTS_VARIABLE = 5
PYGMENTS_STRING = 6
PYGMENTS_ESCAPE = 7
PYGMENTS_REGEX = 8
PYGMENTS_NUMBER = 9
PYGMENTS_LITERAL = 10


class PyLexer(QsciLexerCustom):
    TOKEN_MAP = {
        Token.Comment: PYGMENTS_COMMENT,
        Token.Comment.Hashbang: PYGMENTS_COMMENT,
        Token.Comment.Multiline: PYGMENTS_COMMENT,
        Token.Comment.Single: PYGMENTS_COMMENT,
        Token.Comment.Special: PYGMENTS_COMMENT,
        Token.Keyword: PYGMENTS_KEYWORD,
        Token.Keyword.Constant: PYGMENTS_KEYWORD,
        Token.Keyword.Declaration: PYGMENTS_KEYWORD,
        Token.Keyword.Namespace: PYGMENTS_KEYWORD,
        Token.Keyword.Pseudo: PYGMENTS_KEYWORD,
        Token.Keyword.Type: PYGMENTS_CLASS,
        Token.Literal: PYGMENTS_LITERAL,
        Token.Literal.Date: PYGMENTS_LITERAL,
        Token.Name.Attribute: PYGMENTS_VARIABLE,
        Token.Name.Builtin: PYGMENTS_FUNCTION,
        Token.Name.Builtin.Type: PYGMENTS_CLASS,
        Token.Name.Builtin.Pseudo: PYGMENTS_VARIABLE,
        Token.Name.Class: PYGMENTS_CLASS,
        Token.Name.Constant: PYGMENTS_VARIABLE,
        Token.Name.Decorator: PYGMENTS_FUNCTION,
        Token.Name.Exception: PYGMENTS_CLASS,
        Token.Name.Function: PYGMENTS_FUNCTION,
        Token.Name.Namespace: PYGMENTS_CLASS,
        Token.Name.Other: PYGMENTS_VARIABLE,
        Token.Name.Property: PYGMENTS_VARIABLE,
        Token.Name.Variable: PYGMENTS_VARIABLE,
        Token.Name.Variable.Class: PYGMENTS_VARIABLE,
        Token.Name.Variable.Global: PYGMENTS_VARIABLE,
        Token.Name.Variable.Instance: PYGMENTS_VARIABLE,
        Token.Number: PYGMENTS_NUMBER,
        Token.Number.Bin: PYGMENTS_NUMBER,
        Token.Number.Float: PYGMENTS_NUMBER,
        Token.Number.Hex: PYGMENTS_NUMBER,
        Token.Number.Integer: PYGMENTS_NUMBER,
        Token.Number.Integer.Long: PYGMENTS_NUMBER,
        Token.Number.Oct: PYGMENTS_NUMBER,
        Token.Operator.Word: PYGMENTS_KEYWORD,
        Token.String: PYGMENTS_STRING,
        Token.String.Char: PYGMENTS_STRING,
        Token.String.Doc: PYGMENTS_STRING,
        Token.String.Double: PYGMENTS_STRING,
        Token.String.Escape: PYGMENTS_ESCAPE,
        Token.String.Interpol: PYGMENTS_STRING,
        Token.String.Other: PYGMENTS_STRING,
        Token.String.Regex: PYGMENTS_REGEX,
        Token.String.Single: PYGMENTS_STRING,
        Token.String.Symbol: PYGMENTS_STRING,
    }

    def __init__(self, editor) -> None:
        super().__init__(editor)

        self.setFont(QFont("Consolas"))
        self.setDefaultPaper(QColor("#1E1E1E"))
        self.setPaper(QColor("#1E1E1E"))
        self.setColor(QColor("#D4D4D4"))

        self.setColor(QColor("#D4D4D4"), PYGMENTS_DEFAULT)
        self.setColor(QColor("#4FC1FF"), PYGMENTS_LITERAL)
        self.setColor(QColor("#9CDCFE"), PYGMENTS_VARIABLE)
        self.setColor(QColor("#B5CEA8"), PYGMENTS_NUMBER)
        self.setColor(QColor("#CE9178"), PYGMENTS_STRING)
        self.setColor(QColor("#D16969"), PYGMENTS_REGEX)
        self.setColor(QColor("#D7BA7D"), PYGMENTS_ESCAPE)
        self.setColor(QColor("#DCDCAA"), PYGMENTS_FUNCTION)
        self.setColor(QColor("#4EC9B0"), PYGMENTS_CLASS)
        self.setColor(QColor("#6A9955"), PYGMENTS_COMMENT)
        self.setColor(QColor("#6796E6"), PYGMENTS_KEYWORD)

        editor.setMarginsBackgroundColor(QColor("#1E1E1E"))
        editor.setMarginsForegroundColor(QColor("#FFFFFF"))
        editor.setCaretLineBackgroundColor(QColor("#2C2C2C"))
        editor.setCaretForegroundColor(QColor("#AAAAAA"))

    def description(self, style) -> str:
        if style == PYGMENTS_DEFAULT:
            return self.tr("Default")
        if style == PYGMENTS_COMMENT:
            return self.tr("Comment")
        if style == PYGMENTS_KEYWORD:
            return self.tr("Keyword")
        if style == PYGMENTS_FUNCTION:
            return self.tr("Function or method name")
        if style == PYGMENTS_CLASS:
            return self.tr("Class name")
        if style == PYGMENTS_VARIABLE:
            return self.tr("Identifier")
        if style == PYGMENTS_STRING:
            return self.tr("String")
        if style == PYGMENTS_ESCAPE:
            return self.tr("Escape")
        if style == PYGMENTS_REGEX:
            return self.tr("Regular expression")
        if style == PYGMENTS_NUMBER:
            return self.tr("Number")
        if style == PYGMENTS_LITERAL:
            return self.tr("Literal")

    def styleText(self, start: int, end: int) -> None:
        self.startStyling(start)

        text = self.editor().text()[start:end]
        while text.startswith("\n"):
            self.setStyling(1, 0)
            text = text[1:]

        for token, txt in PythonLexer().get_tokens(text):
            self.setStyling(len(txt), self.TOKEN_MAP.get(token, PYGMENTS_DEFAULT))