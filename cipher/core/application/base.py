from __future__ import annotations
import logging
import zipfile
import io
import sys
import os

from psutil import process_iter
import requests
from PyQt6.QtWidgets import QApplication


class BaseApplication(QApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationDisplayName("Cipher")
        self.setApplicationName("Cipher")
        self.setApplicationVersion("1.4.0")

    @staticmethod
    def getApplication() -> BaseApplication:
        processes = tuple(process.name() for process in process_iter())
        # fmt:off
        if processes.count("Cipher.exe") > 1:
            from .client import ClientApplication
            return ClientApplication(sys.argv)
        
        from .server import ServerApplication
        return ServerApplication(sys.argv)
        # fmt: on

    @property
    def localAppData(self) -> str:
        if not hasattr(self, "_localAppData"):
            if sys.platform == "win32":
                _env = os.getenv("LocalAppData")
                self._localAppData = os.path.join(_env, "Cipher")
            elif sys.platform == "linux":
                _env = os.getenv("HOME")
                self._localAppData = os.path.join(_env, "Cipher")
            else:
                raise NotADirectoryError("MacOS isn't Supported")

            if not os.path.exists(self._localAppData):
                req = requests.get(
                    "https://github.com/Srpboyz/Cipher/releases/latest/download/LocalAppData.zip"
                )
                req.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(req.content)) as zip_file:
                    zip_file.extractall(_env)

            sys.path.insert(0, os.path.join(self._localAppData, "include"))
            sys.path.insert(0, os.path.join(self._localAppData, "site-packages"))

            logging.basicConfig(
                filename=os.path.join(self._localAppData, "logs.log"),
                format="%(levelname)s:%(asctime)s: %(message)s",
                level=logging.ERROR,
            )
        return self._localAppData
