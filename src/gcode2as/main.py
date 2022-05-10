import logging
import sys
import argparse
from os import path

from progress.bar import IncrementalBar

from . import __version__
from .parser import parse
from .converter import Converter

FILE_PATH = "file_path"
OUTPUT_PATH = "output_file_dir"
MIN_DIST = "minimum_distance"
SIGNAL = "signal"
DEBUG_MODE = "debug_mode"


def parse_system_args(args):
    """This function parses the command line arguments given to this script"""
    # program name and description
    arg_parser = argparse.ArgumentParser(description="This script converts G-Code to Kawasaki AS Code")
    # version
    arg_parser.add_argument('--version', action='version', version=f"gcode2as: {__version__}")

    # input file
    arg_parser.add_argument('-f', '--file',
                            dest=FILE_PATH,
                            type=str,
                            required=True,
                            help="The source G-Code file to read"
                            )

    # output file
    arg_parser.add_argument('-o', '--output',
                            dest=OUTPUT_PATH,
                            type=str,
                            help="The path of the directory of the output file"
                            )

    # minimum distance
    arg_parser.add_argument('--min_dist',
                            dest=MIN_DIST,
                            type=float,
                            default=0.0,
                            help="The minimum distance between two points in a G-Code command. Under this value"
                                 "the command gets omitted from the AS code")

    # extrusion signal
    arg_parser.add_argument('-s', '--signal',
                            dest=SIGNAL,
                            type=int,
                            default=2001,
                            help="The signal number to turn on when there is an [E]xtrude command in the G-Code")

    # debug mode
    arg_parser.add_argument('-d', '--debug',
                            dest=DEBUG_MODE,
                            action='store_true',
                            help="Use this flag to include the original G-Code line in the AS program")

    return arg_parser.parse_args(args)


def create_line_generator(file_path: str):
    """Creates a generator object to generate lines from the read file"""

    with open(file_path, 'r') as file:
        for line in file:
            yield line


def main():
    args = parse_system_args(sys.argv[1:])
    file_path = vars(args)[FILE_PATH]
    file_dir, file_name = path.split(file_path)

    output_dir = vars(args)[OUTPUT_PATH]
    if output_dir is None:
        output_dir = file_dir

    if not path.exists(file_path):
        logging.error("Could not open file: %s, the file does not exist", file_path)
        exit(1)

    debug_mode = vars(args)[DEBUG_MODE]

    min_dist = vars(args)[MIN_DIST]

    signal = vars(args)[SIGNAL]

    # get the line count
    line_generator = create_line_generator(file_path)
    line_count = sum(buffer.count("\n") for buffer in line_generator)

    try:
        converter = Converter(program_name=path.splitext(file_name)[0],
                              output_file_path=output_dir,
                              extrude_signal=signal,
                              min_dist=min_dist,
                              debug=debug_mode
                              )

    except PermissionError as e:
        logging.error(f"Got a permission error while trying to open a file ({e})")
        return

    line_generator = create_line_generator(file_path)

    logging.info("Starting conversion...")

    progress_bar = IncrementalBar("Converting", max=line_count)

    for i, line in enumerate(line_generator):
        try:
            parsed_line = parse(line)
            converter.convert_parsed_line(parsed_line)

        except ValueError:
            pass

        if i % 100 == 0 and i != 0:
            progress_bar.next(n=100)

    print()

    converter.close()