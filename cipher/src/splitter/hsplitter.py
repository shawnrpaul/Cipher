from __future__ import annotations
from typing import TYPE_CHECKING
from .base import BaseSplitter, Qt

if TYPE_CHECKING:
    from ..window import Window


class HSplitter(BaseSplitter):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setObjectName("HSplitter")
        self.setOrientation(Qt.Orientation.Horizontal)
