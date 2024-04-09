from pathlib import Path
import json

from PyQt6.QtWidgets import QFrame, QVBoxLayout
from .option import ListOption, CheckBoxOption


class SettingsView(QFrame):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        with open(path) as f:
            self._settings = json.load(f)

        for name, setting in self._settings.items():
            if isinstance(setting, bool):
                option = CheckBoxOption(self, name, setting)
                option.updated.connect(self._changeBool)
                layout.addWidget(option)
            elif isinstance(setting, list):
                option = ListOption(self, name, setting)
                option.added.connect(self._addToList)
                option.updated.connect(self._updateList)
                option.removed.connect(self._removeFromList)
                layout.addWidget(option)

    def _changeBool(self, name: str, value: bool) -> None:
        """Changes the value of a boolean setting

        Parameters
        ----------
        name : str
            Name of the settings
        value : bool
            The boolean value to set
        """
        self._settings[name] = value
        self._saveSettings()

    def _addToList(self, name: str, value: str) -> None:
        """Adds a value to the specified list

        Parameters
        ----------
        name : str
            Name of the setting
        value : str
            The value to append
        """
        self._settings[name].append(value)
        self._saveSettings()

    def _updateList(self, name: str, prevValue: str, newValue: str) -> None:
        """Updates a value to the specified list

        Parameters
        ----------
        name : str
            Name of the setting
        prevValue : str
            The value to update
        newValue : str
            The new value
        """
        try:
            lst: list[str] = self._settings[name]
            lst[lst.index(prevValue)] = newValue
            self._saveSettings()
        except Exception as e:
            ...

    def _removeFromList(self, name: str, value: str) -> None:
        """Remove a value to the specified list

        Parameters
        ----------
        name : str
            Name of the setting
        value : str
            The value to remove
        """
        try:
            self._settings[name].remove(value)
            self._saveSettings()
        except Exception:
            ...

    def _saveSettings(self) -> None:
        """Saves the updated settings"""
        with open(self.path, "w") as f:
            json.dump(self._settings, f, indent=4)
