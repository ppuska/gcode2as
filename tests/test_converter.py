from gcode2as.parser import parse
from gcode2as.converter import Converter


def test_converter():
    c = Converter(program_name="test", output_file_path="gcode")
    with open("gcode/test.gcode") as file:
        for line in file:
            parsed = parse(line)
            c.convert_parsed_line(parsed)

    c.close()


if __name__ == '__main__':
    test_converter()
