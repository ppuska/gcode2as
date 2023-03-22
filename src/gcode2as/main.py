"""Main module of the script"""

import io
from pathlib import Path
from typing import Dict, List
import click
from colorama import Back, Style
import inquirer

from pyfiglet import Figlet
from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.fdm import FDM
from gcode2as.cli.laser_cut import LaserCut
from gcode2as.cli.metal import Metal
from gcode2as.formatter import format_program


from . import __version__

FILE_PATH = "file_path"
OUTPUT_PATH = "output_file_dir"
MIN_DIST = "minimum_distance"
EXTRUDE_SIGNAL = "extrude_signal"
RETRACT_SIGNAL = "retract_signal"
OVERRIDE_SPEED = "override_speed"
DEBUG_MODE = "debug_mode"

DEFAULT_MIN_DISTANCE = 2


@click.command
@click.argument('file', type=click.File())
@click.option('-d', is_flag=True, default=False, help="Use the default values for the options")
@click.option('-v', is_flag=True, default=False, help="More verbosity in the generated code")
def cli(file: io.TextIOWrapper, d: bool, v: bool):

    # display fancy logo
    click.echo(Figlet(justify='center').renderText("gcode2as by Lasram"))

    modes: List[CLICommand] = [FDM(), Metal(), LaserCut()]

    filepath = Path(file.name)
    filename = filepath.stem

    mode_key = 'mode'
    min_distance_key = 'min_dist'
    use_different_output_key = 'use_different_output'
    out_dir_key = 'output'

    # select mode
    questions = [
        inquirer.List(
            mode_key,
            message='What mode would you like to use?',
            choices=[mode.message for mode in modes]),
        inquirer.Text(
            min_distance_key,
            message="Enter the minimum distance for simplifying the toolpaths: ",
            default=DEFAULT_MIN_DISTANCE,
            ignore=d
        ),
        inquirer.Confirm(
            use_different_output_key,
            message='Would you like to use a different directory to save the generated file?',
            default=False
        ),
        inquirer.Path(
            out_dir_key,
            message="Enter the directory for the generated file",
            path_type=inquirer.Path.DIRECTORY,
            exists=True,
            ignore=lambda answers: not answers[use_different_output_key],
        )
    ]

    answers: Dict[str, str] | None = inquirer.prompt(questions)

    if answers is None:
        return

    selected = [mode for mode in modes if mode.message ==
                answers[mode_key]][0]  # the list should only have one element

    min_distance = answers[min_distance_key]
    out_dir = answers.get(out_dir_key)

    lines_as = selected.execute(
        options=CLICommandOptions(
            file=file,
            min_distance=float(min_distance),
            verbose=v
        )
    )

    if lines_as is None:
        return

    formatted = format_program(lines_as, filename)

    if out_dir is None:
        out_dir = filepath.absolute().parent

    # save the file
    out_path = out_dir.joinpath(f'{filename}.pg')
    click.echo(
        f'Saving generated file as {Back.WHITE}{out_path}{Style.RESET_ALL}'
    )
    with open(out_path, 'w', encoding='utf8') as f_open:
        f_open.write(formatted)
