from .lexer import JSONLexer


def run(*args, **kwargs) -> JSONLexer:
    return JSONLexer(*args, **kwargs)
