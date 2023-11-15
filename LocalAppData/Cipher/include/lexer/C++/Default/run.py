from .lexer import CPPLexer


def run(*args, **kwargs) -> CPPLexer:
    return CPPLexer(*args, **kwargs)
