from pygments.lexers.javascript import JavascriptLexer
from pygments.token import Token
from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont

PYGMENTS_DEFAULT = 0
PYGMENTS_COMMENT = 1
PYGMENTS_PREPROCESSOR = 2
PYGMENTS_KEYWORD = 3
PYGMENTS_PSEUDOKEYWORD = 4
PYGMENTS_TYPEKEYWORD = 5
PYGMENTS_OPERATOR = 6
PYGMENTS_WORD = 7
PYGMENTS_BUILTIN = 8
PYGMENTS_FUNCTION = 9
PYGMENTS_CLASS = 10
PYGMENTS_NAMESPACE = 11
PYGMENTS_EXCEPTION = 12
PYGMENTS_VARIABLE = 13
PYGMENTS_CONSTANT = 14
PYGMENTS_LABEL = 15
PYGMENTS_ENTITY = 16
PYGMENTS_ATTRIBUTE = 17
PYGMENTS_TAG = 18
PYGMENTS_DECORATOR = 19
PYGMENTS_STRING = 20
PYGMENTS_DOCSTRING = 21
PYGMENTS_SCALAR = 22
PYGMENTS_ESCAPE = 23
PYGMENTS_REGEX = 24
PYGMENTS_SYMBOL = 25
PYGMENTS_OTHER = 26
PYGMENTS_NUMBER = 27
PYGMENTS_HEADING = 28
PYGMENTS_SUBHEADING = 29
PYGMENTS_DELETED = 30
PYGMENTS_INSERTED = 31
PYGMENTS_GENERIC_ERROR = 40
PYGMENTS_EMPHASIZE = 41
PYGMENTS_STRONG = 42
PYGMENTS_PROMPT = 43
PYGMENTS_OUTPUT = 44
PYGMENTS_TRACEBACK = 45
PYGMENTS_ERROR = 46
PYGMENTS_MULTILINECOMMENT = 47
PYGMENTS_PROPERTY = 48
PYGMENTS_CHAR = 49
PYGMENTS_HEREDOC = 50
PYGMENTS_PUNCTUATION = 51
PYGMENTS_HASHBANG = 52
PYGMENTS_RESERVEDKEYWORD = 53
PYGMENTS_LITERAL = 54
PYGMENTS_DOUBLESTRING = 55
PYGMENTS_SINGLESTRING = 56
PYGMENTS_BACKTICKSTRING = 57
PYGMENTS_WHITESPACE = 58

class JSLexer(QsciLexerCustom):
    TOKEN_MAP = {
        Token.Comment: PYGMENTS_COMMENT,
        Token.Comment.Hashbang: PYGMENTS_COMMENT,
        Token.Comment.Multiline: PYGMENTS_COMMENT,
        Token.Comment.Single: PYGMENTS_COMMENT,
        Token.Comment.Special: PYGMENTS_COMMENT,
        Token.Error: PYGMENTS_ERROR,
        Token.Keyword: PYGMENTS_KEYWORD,
        Token.Keyword.Constant: PYGMENTS_KEYWORD,
        Token.Keyword.Declaration: PYGMENTS_KEYWORD,
        Token.Keyword.Namespace: PYGMENTS_KEYWORD,
        Token.Keyword.Pseudo: PYGMENTS_KEYWORD,
        Token.Keyword.Reserved: PYGMENTS_KEYWORD,
        Token.Keyword.Type: PYGMENTS_CLASS,
        Token.Literal: PYGMENTS_LITERAL,
        Token.Literal.Date: PYGMENTS_LITERAL,
        Token.Name: PYGMENTS_DEFAULT,
        Token.Name.Attribute: PYGMENTS_ATTRIBUTE,
        Token.Name.Builtin: PYGMENTS_VARIABLE,
        Token.Name.Builtin.Pseudo: PYGMENTS_VARIABLE,
        Token.Name.Class: PYGMENTS_CLASS,
        Token.Name.Constant: PYGMENTS_CONSTANT,
        Token.Name.Decorator: PYGMENTS_DECORATOR,
        Token.Name.Entity: PYGMENTS_ENTITY,
        Token.Name.Exception: PYGMENTS_CLASS,
        Token.Name.Function: PYGMENTS_FUNCTION,
        Token.Name.Label: PYGMENTS_LABEL,
        Token.Name.Namespace: PYGMENTS_NAMESPACE,
        # Token.Name.Other: PYGMENTS_VARIABLE,
        Token.Name.Property: PYGMENTS_PROPERTY,
        Token.Name.Tag: PYGMENTS_TAG,
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
        Token.String.Backtick: PYGMENTS_STRING,
        Token.String.Char: PYGMENTS_CHAR,
        Token.String.Doc: PYGMENTS_DOCSTRING,
        Token.String.Double: PYGMENTS_STRING,
        Token.String.Escape: PYGMENTS_ESCAPE,
        Token.String.Heredoc: PYGMENTS_HEREDOC,
        Token.String.Interpol: PYGMENTS_STRING,
        Token.String.Other: PYGMENTS_OTHER,
        Token.String.Regex: PYGMENTS_REGEX,
        Token.String.Single: PYGMENTS_STRING,
        Token.String.Symbol: PYGMENTS_SYMBOL,
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
        self.setColor(QColor("#4FC1FF"), PYGMENTS_CONSTANT)
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
        for token, txt in JavascriptLexer().get_tokens(text):
            style = self.TOKEN_MAP.get(token, PYGMENTS_DEFAULT)
            self.setStyling(len(txt), style)