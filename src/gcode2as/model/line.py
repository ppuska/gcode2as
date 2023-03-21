"""Module for the modeling and parsing of a single line of G code"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re


class MoveType(Enum):
    """Enum class of the supported G code move types"""

    G0 = "G0"
    G1 = "G1"


@dataclass
class Line:  # pylint: disable=too-many-instance-attributes
    """Represents a single line of G code"""

    move_type: MoveType = field(default=MoveType.G0)
    x_prop: float = field(default=None)
    y_prop: float = field(default=None)
    z_prop: float = field(default=None)
    e_prop: float = field(default=None)
    f_prop: float = field(default=None)
    s_prop: float = field(default=None)

    comment: str = field(default="")

    raw: str = field(default="")

    valid: bool = field(default=False)

    def __str__(self) -> str:
        string = f"{self.move_type.value} "
        if self.x_prop is not None:
            string += f"X{self.x_prop} "
        if self.y_prop is not None:
            string += f"Y{self.y_prop} "
        if self.z_prop is not None:
            string += f"Z{self.z_prop} "
        if self.e_prop is not None:
            string += f"E{self.e_prop} "
        if self.f_prop is not None:
            string += f"F{self.f_prop} "
        if self.comment:
            string += f";{self.comment}"

        return string

    @classmethod
    def parse(cls, source: str, previous: Line | None = None):
        """Parses a single line of G code

        Args:
            source (str): The raw string of g code
            previous (Line | None, optional): The previous line object from the file.
            Defaults to None.

        Returns:
            _type_: The parsed line object
        """
        # create the instance of the class
        instance = cls()

        instance.raw = source[:-1]

        # search for comments
        comment_start = source.find(";")
        if comment_start != -1:
            instance.comment = source[comment_start + 1 : -1]

        # search for the movetype first
        for move_type in MoveType:
            if move_type.value in source:
                instance.move_type = move_type
                Line.__process_values(instance, source)
                instance.valid = True
                break

        if previous is None:
            previous = Line(MoveType.G0, 0, 0, 0, 0, 0, 0)

        # fill in the missing data from the previous line
        if instance.x_prop is None:
            instance.x_prop = previous.x_prop

        if instance.y_prop is None:
            instance.y_prop = previous.y_prop

        if instance.z_prop is None:
            instance.z_prop = previous.z_prop

        return instance

    @staticmethod
    def __process_values(line: Line, source: str):
        """Parses and fills the fields of the given line object

        Args:
            line (Line): The line object to set the parsed values into
            source (str): The raw string of the G code
        """
        line.x_prop = Line.__find_float("x", source)
        line.y_prop = Line.__find_float("y", source)
        line.z_prop = Line.__find_float("z", source)
        line.e_prop = Line.__find_float("e", source)
        line.f_prop = Line.__find_float("f", source)

    @staticmethod
    def __find_float(prefix: str, where: str) -> float | None:
        """Finds a float value in the source string using regex

        Args:
            prefix (str): The prefix of the gcode command
            where (str): The source string to search the expression in

        Returns:
            float | None: The found float or None if it was not found
        """
        pattern = prefix.upper() + r"(-?\d*(\.\d+)?)"
        regex = re.compile(pattern)
        matches = regex.search(where)

        if matches is not None:
            return float(matches.group(0)[1:])

        return None

    def to_as_command(self, debug=False) -> str:
        """Converts the line object to an AS command formatted string

        Args:
            debug (bool, optional): If enabled the raw string will be attached
            as comment to the end of the line. Defaults to False.

        Returns:
            str: The line object formatted as AS command
        """
        if debug:
            ending = self.raw
        else:
            ending = self.comment

        return f"LMOVE SHIFT(a BY {self.x_prop}, {self.y_prop}, {self.z_prop}) ; {ending}\n"
