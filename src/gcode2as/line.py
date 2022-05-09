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
