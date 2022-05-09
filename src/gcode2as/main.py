import logging
import sys
import argparse
from os import path

import gcode2as
from gcode2as.parser import parse

FILE_PATH = "file_path"


def parse_system_args(args):
    """This function parses the command line arguments given to this script"""
    # program name and description
    arg_parser = argparse.ArgumentParser(description="This script converts G-Code to Kawasaki AS Code")
    # version
    arg_parser.add_argument('--version', action='version', version=f"gcode2as: {gcode2as.__version__}")

    # input file
    arg_parser.add_argument('-f', '--file',
                            dest=FILE_PATH,
                            type=str,
                            required=True,
                            help="The source G-Code file to read"
                            )

    return arg_parser.parse_args(args)


def create_line_generator(file_path: str):
    """Creates a generator object to generate lines from the read file"""

    with open(file_path, 'r') as file:
        for line in file:
            yield line


def main():
    args = parse_system_args(sys.argv[1:])
    file_path = vars(args)[FILE_PATH]

    if not path.exists(file_path):
        logging.error("Could not open file: %s, the file does not exist", file_path)
        exit(1)

    line_generator = create_line_generator(file_path)

    for line in line_generator:
        print(parse(line))
