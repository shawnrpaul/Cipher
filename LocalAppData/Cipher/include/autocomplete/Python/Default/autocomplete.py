from PyQt6.QtCore import QThread
from PyQt6.Qsci import QsciAPIs
from jedi import Project, Script
from pathlib import Path
import os

class PyAutoCompleter(QThread):
    def __init__(self, editor, api: QsciAPIs, path: Path, project: str, *args, **kwargs) -> None:
        super().__init__(editor)
        self.editor = editor
        self.api = api
        self.path = path
        localappdata = os.getenv("LocalAppData")
        python = os.path.join(localappdata, "Programs", "Python")
        self.project = (
            Project.load(project)
            if project
            else Project(
                path=path,
                sys_path=[
                    "",
                    f"{localappdata}\\Programs\\Python\\{python[0]}\\{python[0].lower()}.zip",
                    f"{localappdata}\\Programs\\Python\\{python[0]}\\Lib",
                    f"{localappdata}\\Programs\\Python\\{python[0]}\\DLLs",
                    f"{localappdata}\\Programs\\Python\\{python[0]}",
                    f"{localappdata}\\Programs\\Python\\{python[0]}\\Lib\\site-packages",
                ],
            )
        )

    def run(self) -> None:
        pos = self.editor.getCursorPosition()
        try:
            script = Script(self.editor.text(), path=self.path, project=self.project)
            self.api.clear()
            for completion in script.complete(pos[0] + 1, pos[1]):
                self.api.add(completion.name)
            self.api.prepare()
        except:
            pass
        self.finished.emit()


def autocomplete(*args, **kwargs) -> PyAutoCompleter:
    return PyAutoCompleter(*args, **kwargs)
