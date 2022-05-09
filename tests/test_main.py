import sys

from gcode2as.main import main

sys.argv = sys.argv[:1]
sys.argv.extend(["-f", "gcode/benchy.gcode", "--min_dist", "2.0", "-s", "2001"])


def test_main():
    main()


if __name__ == '__main__':
    test_main()
