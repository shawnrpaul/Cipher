from .lexer import JSLexer


def run(*args, **kwargs) -> JSLexer:
    return JSLexer(*args, **kwargs)
