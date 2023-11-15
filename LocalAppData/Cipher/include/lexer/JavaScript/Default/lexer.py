from PyQt6.Qsci import QsciLexerJavaScript
from PyQt6.QtGui import QColor, QFont
from typing import Dict
from pathlib import Path
import json


class JSLexer(QsciLexerJavaScript):
    def __init__(self, editor) -> None:
        super().__init__(editor)

        styles = getStyling()

        self.setFont(QFont(styles.get("font")))
        self.setPaper(QColor(styles.get("paper")))
        self.setDefaultPaper(QColor(styles.get("paper")))
        self.setColor(QColor(styles.get("default")))
        self.setDefaultColor(QColor(styles.get("default")))

        self.setColor(QColor(styles.get("num")), self.Number)
        self.setColor(QColor(styles.get("num")), self.InactiveNumber)

        self.setColor(QColor(styles.get("class")), self.GlobalClass)
        self.setColor(QColor(styles.get("class")), self.InactiveGlobalClass)

        self.setColor(QColor(styles.get("keyword")), self.Keyword)
        self.setColor(QColor(styles.get("keyword")), self.InactiveKeyword)
        self.setColor(QColor(styles.get("keyword")), self.KeywordSet2)
        self.setColor(QColor(styles.get("keyword")), self.InactiveKeywordSet2)

        self.setColor(QColor(styles.get("preprocessor")), self.PreProcessor)
        self.setColor(QColor(styles.get("preprocessor")), self.InactivePreProcessor)

        self.setColor(QColor(styles.get("comment")), self.Comment)
        self.setColor(QColor(styles.get("comment")), self.InactiveComment)
        self.setColor(QColor(styles.get("comment")), self.CommentLine)
        self.setColor(QColor(styles.get("comment")), self.InactiveCommentLine)
        self.setColor(QColor(styles.get("comment")), self.CommentDoc)
        self.setColor(QColor(styles.get("comment")), self.InactiveCommentDoc)
        self.setColor(QColor(styles.get("comment")), self.CommentLineDoc)
        self.setColor(QColor(styles.get("comment")), self.InactiveCommentLineDoc)
        self.setColor(QColor(styles.get("comment")), self.CommentDocKeyword)
        self.setColor(QColor(styles.get("comment")), self.InactiveCommentDocKeyword)
        self.setColor(QColor(styles.get("comment")), self.CommentDocKeywordError)
        self.setColor(
            QColor(styles.get("comment")), self.InactiveCommentDocKeywordError
        )
        self.setColor(QColor(styles.get("comment")), self.PreProcessorComment)
        self.setColor(QColor(styles.get("comment")), self.InactivePreProcessorComment)
        self.setColor(QColor(styles.get("comment")), self.PreProcessorCommentLineDoc)
        self.setColor(
            QColor(styles.get("comment")), self.InactivePreProcessorCommentLineDoc
        )

        self.setColor(QColor(styles.get("string")), self.DoubleQuotedString)
        self.setColor(QColor(styles.get("string")), self.InactiveDoubleQuotedString)
        self.setColor(QColor(styles.get("string")), self.SingleQuotedString)
        self.setColor(QColor(styles.get("string")), self.InactiveSingleQuotedString)
        self.setColor(QColor(styles.get("string")), self.UnclosedString)
        self.setColor(QColor(styles.get("string")), self.InactiveUnclosedString)
        self.setColor(QColor(styles.get("string")), self.VerbatimString)
        self.setColor(QColor(styles.get("string")), self.InactiveVerbatimString)
        self.setColor(QColor(styles.get("string")), self.RawString)
        self.setColor(QColor(styles.get("string")), self.InactiveRawString)
        self.setColor(QColor(styles.get("string")), self.TripleQuotedVerbatimString)
        self.setColor(
            QColor(styles.get("string")), self.InactiveTripleQuotedVerbatimString
        )
        self.setColor(QColor(styles.get("string")), self.HashQuotedString)
        self.setColor(QColor(styles.get("string")), self.InactiveHashQuotedString)

        editor.setMarginsBackgroundColor(QColor(styles.get("paper")))
        editor.setMarginsForegroundColor(QColor(styles.get("margin")))
        editor.setCaretLineBackgroundColor(QColor(styles.get("caretBackground")))
        editor.setCaretForegroundColor(QColor(styles.get("caretForeground")))


def getStyling() -> Dict[str, str]:
    with open(f"{Path(__file__).absolute().parent}/syntax.json") as f:
        return json.load(f)
