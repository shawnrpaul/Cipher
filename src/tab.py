from PyQt6.QtWidgets import QTabWidget

__all__ = ("TabWidget",)


class TabWidget(QTabWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.tabCloseRequested.connect(self.removeTab)
