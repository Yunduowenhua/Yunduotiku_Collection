from dataclasses import dataclass, field
from typing import Tuple, List

@dataclass
class CanonicalRect:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self):
        if self.x0 > self.x1:
            self.x0, self.x1 = self.x1, self.x0
        if self.y0 > self.y1:
            self.y0, self.y1 = self.y1, self.y0

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def intersects(self, other: "CanonicalRect") -> bool:
        return not (self.x1 < other.x0 or self.x0 > other.x1 or self.y1 < other.y0 or self.y0 > other.y1)

    def union(self, other: "CanonicalRect") -> "CanonicalRect":
        return CanonicalRect(
            x0=min(self.x0, other.x0),
            y0=min(self.y0, other.y0),
            x1=max(self.x1, other.x1),
            y1=max(self.y1, other.y1)
        )

@dataclass
class TextBlock:
    rect: CanonicalRect
    text: str
    block_type: int = 0
