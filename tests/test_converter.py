import logging

from gcode2as.parser import parse
from gcode2as.converter import Converter


def test_converter():
    c = Converter(program_name="benchy", output_file_path="gcode", debug=True)
    with open("gcode/benchy.gcode") as file:
        for i, line in enumerate(file):
            try:
                parsed = parse(line)
            except ValueError:
                logging.warning("Parse error at line: %i -> %s", i, line[:-1])

            else:
                c.convert_parsed_line(parsed)

    c.close()


if __name__ == '__main__':
    test_converter()
