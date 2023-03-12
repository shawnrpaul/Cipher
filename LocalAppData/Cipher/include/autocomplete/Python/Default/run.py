from .autocomplete import PyAutoCompleter


def run(*args, **kwargs) -> PyAutoCompleter:
    return PyAutoCompleter(*args, **kwargs)
