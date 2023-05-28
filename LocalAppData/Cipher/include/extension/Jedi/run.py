from .jedi import Jedi


def run(*args, **kwargs) -> Jedi:
    return Jedi(*args, **kwargs)
