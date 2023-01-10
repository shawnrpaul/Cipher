from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

__all__ = ("Body",)


class Body(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Body")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setLineWidth(0)
        self.setMidLineWidth(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def setLayout(self) -> None:
        return super().setLayout(self._layout)
