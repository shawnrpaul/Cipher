from __future__ import annotations
from typing import TYPE_CHECKING
import json

from PyQt6.QtNetwork import QHostAddress
from PyQt6.QtWebSockets import QWebSocketServer

if TYPE_CHECKING:
    from .application import ServerApplication


class PortError(Exception):
    def __init__(self, port: int) -> None:
        super().__init__(f"Port {port} is already in use")


class Server(QWebSocketServer):
    def __init__(self, app: ServerApplication) -> None:
        super().__init__("Cipher Server", QWebSocketServer.SslMode.NonSecureMode, app)

    @property
    def application(self) -> ServerApplication:
        return self.parent()

    app = application

    def setPort(self, port: int) -> None:
        self.port = port

    def listen(self) -> None:
        if not super().listen(QHostAddress.SpecialAddress.LocalHost, self.port):
            raise PortError(self.port)
        self.newConnection.connect(self.onNewConnection)
        self.closed.connect(self.application.close)
        self.client = None

    def onNewConnection(self) -> None:
        self.client = self.nextPendingConnection()
        self.client.textMessageReceived.connect(self.processTextMessage)
        self.client.disconnected.connect(self.socketDisconnected)

    def processTextMessage(self, message: str) -> None:
        if not self.client:
            return
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            self.client.sendTextMessage(
                json.dumps(
                    {"code": 404, "message": "Recieved data isn't in JSON format"}
                )
            )
            return self.client.disconnect()

        if argv := data.get("argv"):
            self.application.parseArgs(argv)

    def sendResponse(self, data: dict):
        if not self.client:
            return
        self.client.sendTextMessage(json.dumps(data))
        self.client.disconnect()

    def socketDisconnected(self):
        if self.client:
            self.client.deleteLater()
        self.client = None
