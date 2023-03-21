"""Testing module for the Line objects"""

from typing import List
import unittest

from gcode2as.model.line import Line
from gcode2as.converter import convert_to_as
from gcode2as.main import format_program

TEST_FILE = "resources/kup.gcode"


class TestLine(unittest.TestCase):
    """Test case for the Line object"""

    test_lines_num = 100_000
    lines = List[Line]
    lines_converted = List[str]

    def setUp(self) -> None:
        self.lines = []
        self.lines_converted = []

    def line_generator(self):
        """Creates a line generator"""
        with open(TEST_FILE, "r", encoding="utf-8") as f_open:
            for line in f_open:
                yield line

    def test_parsing(self):
        """Tests the parse method of the Line object"""
        prev_line = None
        for i, line_str in enumerate(self.line_generator()):
            if i >= TestLine.test_lines_num:
                return

            line = Line.parse(line_str, prev_line)
            prev_line = line
            self.lines.append(line)

    def test_converting(self):
        """Tests the convert_to_as method of the Line object"""
        self.test_parsing()
        self.lines_converted = convert_to_as(
            self.lines, 0, 1, min_dist=2, verbose=True)

    def test_formatting(self):
        """Test the test_formatting method from the main module"""
        self.test_converting()
        as_file = format_program(self.lines_converted, "test")

        with open("generated/result.pg", "w", encoding="utf-8") as f_open:
            f_open.write(as_file)


if __name__ == "__main__":
    unittest.main()
