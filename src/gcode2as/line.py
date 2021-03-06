from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Line:
    """Data class to store a parsed G-Code line"""

    G0: ClassVar[str] = 'G0'
    G1: ClassVar[str] = 'G1'

    X: ClassVar[str] = 'X'
    Y: ClassVar[str] = 'Y'
    Z: ClassVar[str] = 'Z'

    F: ClassVar[str] = 'F'

    E: ClassVar[str] = 'E'

    move_type: str = field(default="")  # the move type token in the line

    geometry: dict = field(default_factory=lambda: {})

    feed: float = field(default=0.0)

    extrude: float = field(default=0.0)

    is_comment: bool = field(default=False)

    raw: str = field(default="")

    @property
    def has_extrude(self):
        return self.extrude > 0

    @property
    def zero_move(self):
        x = self.geometry.get(self.X)
        y = self.geometry.get(self.Y)
        z = self.geometry.get(self.Z)

        if x is not None and x != 0.0:
            return False

        if y is not None and y != 0.0:
            return False

        if z is not None and z != 0.0:
            return False

        return True
