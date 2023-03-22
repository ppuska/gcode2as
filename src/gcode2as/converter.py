"""Module for converting Line objects to AS code"""

from io import TextIOWrapper
from typing import Callable, List
from math import sqrt
from click import echo
from colorama import Back
from gcodeparser import GcodeLine, GcodeParser
from progress.bar import IncrementalBar


class Converter:
    __gcode: GcodeParser | None

    def __init__(self, file: TextIOWrapper) -> None:
        self.__gcode = GcodeParser(file.read(), include_comments=True)

    def convert(self, line_processor: Callable[[GcodeLine], str | List[str]]):
        if self.__gcode is None:
            echo(f'{Back.YELLOW}No GCODE is loaded.')
            return None

        converted_lines: List[str] = []

        for gcode_line in self.__gcode.lines:
            processed_line = line_processor(gcode_line)

            # check if the returned value is a list
            if isinstance(processed_line, list):
                processed_line = [
                    line if line.endswith('\n') else f'{line}\n' for line in processed_line
                ]

            # the returned value is a string
            elif not processed_line.endswith('\n'):
                processed_line += '\n'

            converted_lines.extend(processed_line)

        return converted_lines

    @property
    def file_length(self):
        return len(self.__gcode.lines)
