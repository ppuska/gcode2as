"""Main module of the script"""

import sys
import argparse
from os import path
from typing import List
from math import ceil

from pyfiglet import Figlet

from gcode2as.model.line import Line
from gcode2as.converter import convert_to_as


from . import __version__

FILE_PATH = "file_path"
OUTPUT_PATH = "output_file_dir"
MIN_DIST = "minimum_distance"
EXTRUDE_SIGNAL = "extrude_signal"
RETRACT_SIGNAL = "retract_signal"
OVERRIDE_SPEED = "override_speed"
DEBUG_MODE = "debug_mode"

MAX_PROGRAM_LENGTH = 1000


def parse_system_args(args):
    """This function parses the command line arguments given to this script"""
    # program name and description
    arg_parser = argparse.ArgumentParser(
        description="This script converts G-Code to Kawasaki AS Code"
    )
    # version
    arg_parser.add_argument(
        "--version", action="version", version=f"gcode2as: {__version__}"
    )

    # input file
    arg_parser.add_argument(
        "-f",
        "--file",
        dest=FILE_PATH,
        type=str,
        required=True,
        help="The source G-Code file to read",
    )

    # output file
    arg_parser.add_argument(
        "-o",
        "--output",
        dest=OUTPUT_PATH,
        type=str,
        help="The path of the directory of the output file",
    )

    # minimum distance
    arg_parser.add_argument(
        "--min-dist",
        dest=MIN_DIST,
        type=float,
        default=0.0,
        help="The minimum distance between two points in a G-Code command. Under this value"
        "the command gets omitted from the AS code",
    )

    # extrusion signal
    arg_parser.add_argument(
        "-e",
        "--extrude",
        dest=EXTRUDE_SIGNAL,
        type=int,
        default=1,
        # pylint: disable=line-too-long
        help="The signal number to turn on when there is a positive [E]xtrude command in the G-Code",
    )

    arg_parser.add_argument(
        "-r",
        "--retract",
        dest=RETRACT_SIGNAL,
        type=int,
        default=2,
        help="The signal number to turn on when there is a retract command (-E) in the G-Code",
    )

    arg_parser.add_argument(
        "--override-speed",
        dest=OVERRIDE_SPEED,
        type=int,
        help="Use this to override the speed settings and create a constant speed",
    )

    # debug mode
    arg_parser.add_argument(
        "-d",
        "--debug",
        dest=DEBUG_MODE,
        action="store_true",
        help="Use this flag to include the original G-Code line in the AS program",
    )

    return arg_parser.parse_args(args)


def create_line_generator(file_path: str):
    """Creates a generator object to generate lines from the read file"""

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            yield line


def format_program(lines: List[str], program_name: str) -> str:
    """Formats the program, and generates a raw string to save to file

    If the program is longer than MAX_PROGRAM_LENGTH then it is split into said length chunks and
    save as subprograms formatted as <program_name>_<subprogram_index>

    Args:
        lines (List[str]): the list os AS commands as strings
        program_name (str): the name of the AS program

    Returns:
        str: the formatted string output of the program
    """
    as_program = ""

    if len(lines) < MAX_PROGRAM_LENGTH:
        as_program = f".PROGRAM {program_name}\n"

        for line in lines:
            as_program += line

        as_program += ".END"
        return as_program

    subprogram_number = ceil(len(lines) / MAX_PROGRAM_LENGTH)

    for i in range(subprogram_number):
        as_program += f".PROGRAM {program_name}_{i}\n"
        as_program += "".join(
            lines[i * MAX_PROGRAM_LENGTH : (i + 1) * MAX_PROGRAM_LENGTH]
        )
        as_program += ".END\n\n"

    as_program += f".PROGRAM {program_name}\n"
    for i in range(subprogram_number):
        as_program += f"CALL {program_name}_{i}\n"

    as_program += ".END\n"

    return as_program


def main():
    """The main entrypoint of the script"""
    args = parse_system_args(sys.argv[1:])

    # display fancy logo
    print(Figlet(font="slant").renderText("gcode2as"))

    file_path = vars(args)[FILE_PATH]
    file_dir, file_name = path.split(file_path)

    output_dir = vars(args)[OUTPUT_PATH]
    if output_dir is None:
        output_dir = file_dir

    debug_mode = vars(args)[DEBUG_MODE]

    min_dist = vars(args)[MIN_DIST]

    extrude_signal = vars(args)[EXTRUDE_SIGNAL]

    retract_signal = vars(args)[RETRACT_SIGNAL]

    override_speed = vars(args)[OVERRIDE_SPEED]

    line_generator = create_line_generator(file_path)

    print(f"Extrude signal set to {extrude_signal}")
    print(f"Retract signal set to {retract_signal}")
    if override_speed is not None:
        print(f"Speed is overridden to {override_speed}")

    lines = []

    for i, line in enumerate(line_generator):
        if i == 0:
            lines.append(Line.parse(line))
        else:
            lines.append(Line.parse(line, lines[i - 1]))

    lines_as = convert_to_as(
        lines, extrude_signal, retract_signal, min_dist, override_speed, debug_mode
    )

    program_name = path.splitext(file_name)[0]

    as_program = format_program(lines_as, program_name)

    with open(f"{output_dir}/{program_name}.pg", "w", encoding="utf-8") as output:
        output.write(as_program)

    print(f"Program saved as {path.join(output_dir, program_name)}.pg")
