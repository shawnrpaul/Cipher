from __future__ import annotations
import json
import sys

from PyQt6.QtCore import QUrl
from PyQt6.QtWebSockets import QWebSocket
from .base import BaseApplication


class Client(QWebSocket):
    def __init__(self, app: ClientApplication) -> None:
        super().__init__(parent=app)
        self.open(QUrl("ws://127.0.0.1:6969"))
        self.connected.connect(self.onConnect)
        self.textMessageReceived.connect(self.parseMessage)

    @property
    def application(self) -> ClientApplication:
        return self.parent()

    app = application

    def onConnect(self) -> None:
        self.sendTextMessage(json.dumps({"code": 0, "argv": sys.argv}))

    def parseMessage(self, message: str) -> None:
        data = json.loads(message)
        self.application.exit()
        if data["code"] != 200:
            print(data["message"], file=sys.stderr)
            return self.application.exit(1)
        return self.application.exit(0)


class ClientApplication(BaseApplication):
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.client = Client(self)
