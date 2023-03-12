from .lexer import DefaultLexer


def run(*args, **kwargs) -> DefaultLexer:
    return DefaultLexer(*args, **kwargs)
