from .formatter import Black


def run(*args, **kwargs) -> Black:
    return Black(*args, **kwargs)
