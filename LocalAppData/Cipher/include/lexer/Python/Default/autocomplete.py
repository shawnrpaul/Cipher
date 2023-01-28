from PyQt6.QtCore import QThread
from PyQt6.Qsci import QsciAPIs
from jedi import find_system_environments, find_virtualenvs, Script
from pathlib import Path
from typing import Dict, List, Union


class PyAutoCompleter(QThread):
    def __init__(
        self,
        api: QsciAPIs,
        path: Path,
        workspace: Dict[str, Union[str, List[str]]] = None,
    ):
        super().__init__()
        self.api = api
        self.path = path
        self.venv = workspace.get("venv")
        self.line = 0
        self.index = 0
        self.text = ""

    def setVenv(self):
        if isinstance(self.venv, str):
            self.venv = tuple(find_virtualenvs([self.venv]))[-1]
        elif self.venv is None:
            self.venv = tuple(find_system_environments())[0]

    def setPos(self, line: int, index: int, text: str):
        self.line = line
        self.index = index
        self.text = text

    def run(self):
        self.setVenv()
        try:
            script = Script(self.text, path=self.path, environment=self.venv)
            self.api.clear()
            for completion in script.complete(self.line, self.index):
                self.api.add(completion.name)
            self.api.prepare()
        except:
            pass
        self.finished.emit()


def autocomplete(*args, **kwargs) -> PyAutoCompleter:
    return PyAutoCompleter(*args, **kwargs)
