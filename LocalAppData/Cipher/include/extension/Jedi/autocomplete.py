from jedi import Project, Script
import os


class PyAutoCompleter:
    def __init__(self, editor, project: str) -> None:
        self.editor = editor
        self.api = editor.api
        self.path = editor.path
        self.enabled = True
        editor.setAutoCompleter(self)
        if project:
            self.project = Project.load(project)
        else:
            python = os.path.join(os.getenv("LocalAppData"), "Programs", "Python")
            python_version = os.listdir(python)
            self.project = Project(
                path=self.path.parent,
                sys_path=[
                    "",
                    f"{python}\\{python[0]}\\{python_version[0].lower()}.zip",
                    f"{python}\\{python_version[0]}\\Lib",
                    f"{python}\\{python_version[0]}\\DLLs",
                    f"{python}\\{python_version[0]}",
                    f"{python}\\{python_version[0]}\\Lib\\site-packages",
                ],
            )

    def run(self) -> None:
        if not self.enabled:
            return
        pos = self.editor.getCursorPosition()
        try:
            script = Script(self.editor.text(), path=self.path, project=self.project)
            self.api.clear()
            for completion in script.complete(pos[0] + 1, pos[1], fuzzy=True):
                self.api.add(completion.name)
            self.api.prepare()
        except Exception as e:
            print(e.__class__, e)


def autocomplete(*args, **kwargs) -> PyAutoCompleter:
    return PyAutoCompleter(*args, **kwargs)
