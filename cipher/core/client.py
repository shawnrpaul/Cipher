from __future__ import annotations
from typing import TYPE_CHECKING
import json
import sys

from PyQt6.QtCore import QUrl
from PyQt6.QtWebSockets import QWebSocket

if TYPE_CHECKING:
    from .application import ClientApplication


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
        self.sendTextMessage(json.dumps({"argv": sys.argv}))

    def parseMessage(self, message: str) -> None:
        data = json.loads(message)
        self.application.close()
        if data["code"] != 200:
            print(data["message"], file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
