from gcode2as.main import parse_system_args

ARGS = ["-f", "gcode/test.gcode"]


# ARGS = ["--version"]

def test_arg_parsing():
    print(vars(parse_system_args(ARGS)))


if __name__ == '__main__':
    test_arg_parsing()
