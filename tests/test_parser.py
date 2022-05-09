from gcode2as.parser import parse

LINE = "G1 X112.711 Y124.027 E2865.10445"


def test_parser():
    print(parse(LINE))


if __name__ == '__main__':
    test_parser()
