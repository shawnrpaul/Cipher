from .base import BaseSplitter, Qt


class VSplitter(BaseSplitter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setObjectName("VSplitter")
        self.setOrientation(Qt.Orientation.Vertical)
