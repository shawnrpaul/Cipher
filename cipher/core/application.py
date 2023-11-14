from typing import List
import asyncio

from PyQt6.QtWidgets import QApplication

__all__ = ("Application",)


class Application(QApplication):
    def __init__(self, argv: List[str]) -> None:
        super().__init__(argv)
        self.isOpen = True

    def close(self):
        self.isOpen = False

    async def eventLoop(self):
        while self.isOpen:
            self.processEvents()
            await asyncio.sleep(0)

    def start(self) -> None:
        asyncio.get_event_loop().run_until_complete(self.eventLoop())
