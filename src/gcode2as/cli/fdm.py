import math
from os import get_terminal_size
from typing import Dict, List, Tuple

from click import echo
from colorama import Back, Style
import inquirer
from gcodeparser.gcode_parser import GcodeLine

from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.utils import inquirer_elements
from gcode2as.cli.utils.validation import validate_is_int
from gcode2as.converter import Converter


class FDM(CLICommand):

    DEFAULT_EXTRUDE_SIGNAL = 2001
    DEFAULT_RETRACT_SIGNAL = 2002

    def __init__(self) -> None:
        self.__is_extruding = False
        self.__x_pos = 0
        self.__y_pos = 0
        self.__z_pos = 0
        self.__e_pos = 0

        self.__override_speed: float | None = None

        self.__skipped_distance = 0
        self.__skipped_moves = 0

        self.__extrude_signal = 0
        self.__retract_signal = 0

        self.__execute_options: CLICommandOptions = None

    @property
    def message(self) -> str:
        return "FDM 3D Printing"

    def execute(self, options: CLICommandOptions):
        self.__execute_options = options

        # keys for the inquirer
        extrude_key = 'extrude'
        retract_key = 'retract'

        questions = [
            inquirer.Text(
                extrude_key,
                message='Specify the extrude signal',
                default=FDM.DEFAULT_EXTRUDE_SIGNAL,
                validate=validate_is_int
            ),
            inquirer.Text(
                retract_key,
                message='Specify the retract signal',
                default=FDM.DEFAULT_RETRACT_SIGNAL,
                validate=validate_is_int,
            ),
            *inquirer_elements.ask_override_speed()
        ]

        answers: Dict[str, str] | None = inquirer.prompt(questions)

        if answers is None:
            return

        self.__extrude_signal = int(answers[extrude_key])
        self.__retract_signal = int(answers[retract_key])

        override_speed = answers.get(
            inquirer_elements.OVERRIDE_SPEED_VALUE_KEY
        )

        echo(f"Extrude signal set to {self.__extrude_signal}")
        echo(f"Retract signal set to {self.__retract_signal}")
        if override_speed is not None:
            echo(f"Speed is overridden to {override_speed}")
            self.__override_speed = float(override_speed)

        converter = Converter(options.file)

        # override the speed
        if self.__override_speed is not None:
            lines = []
            lines.append(
                f'SPEED {self.__override_speed} MM/MIN ALWAYS ; Master speed override\n'
            )

        lines = converter.convert(self.__process_line)

        linewidth = get_terminal_size().columns

        echo(f'Conversion {Back.GREEN}done{Style.RESET_ALL}.')
        echo('*' * linewidth)
        echo(f'{Back.CYAN}Stats:{Style.RESET_ALL}')
        echo(f'\tGCODE file had {converter.file_length} lines')
        echo(f'\tOmitted {self.__skipped_moves} lines')
        echo(f'\tAS file length is {len(lines)} lines')
        echo('*' * linewidth)

        return lines

    def __process_line(self, line: GcodeLine):

        processed_lines: List[str] = []

        # check for parameters
        feed = line.params.get('F')
        extrude = line.params.get('E')
        position = (
            line.params.get('X'),
            line.params.get('Y'),
            line.params.get('Z')
        )

        # process comment-only lines
        if line.command[0] == ';':
            processed_lines.append(f'; {line.comment}')

        # process G0 commands
        elif line.command[0] == 'G' and line.command[1] == 0:
            processed_lines.extend(
                self.__process_g0(
                    line,
                    feed,
                    position
                )
            )

        # process G1 commmand
        elif line.command[0] == 'G' and line.command[1] == 1:
            processed_lines.extend(
                self.__process_g1(
                    line,
                    feed,
                    extrude,
                    position
                )
            )

        # process G2 command
        elif line.command[0] == 'G' and line.command[1] == 2:
            echo(f'{Back.YELLOW}G2 command is not implemented{Style.RESET_ALL}')

        return processed_lines

    def __process_g0(
            self,
            line: GcodeLine,
            feed: float | None,
            position: Tuple[float | None, float | None, float | None]
    ):
        lines = []
        x_pos, y_pos, z_pos = position

        # feed
        if feed is not None and self.__override_speed is None:
            # append the command
            lines.append(f'SPEED {feed} MM/MIN ALWAYS')

        # xyz positions
        self.__x_pos = x_pos if x_pos is not None else self.__x_pos
        self.__y_pos = y_pos if y_pos is not None else self.__y_pos
        self.__z_pos = z_pos if z_pos is not None else self.__z_pos

        move_command = f'LMOVE SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos})'

        if line.comment:
            move_command += f' ;{line.command}'

        move_command += '\n'

        lines.append(move_command)

        return lines

    def __process_g1(
            self,
            line: GcodeLine,
            feed: float | None,
            extrude: float | None,
            position: Tuple[float | None, float | None, float | None]
    ):
        lines = []

        x_pos, y_pos, z_pos = position

        # feed
        if feed is not None and self.__override_speed is None:
            # append the command
            lines.append(f'SPEED {feed} MM/MIN ALWAYS\n')

        # extrusion
        if extrude is not None and extrude > self.__e_pos:
            # update the extrusion value
            self.__e_pos = extrude

            # extrusion start
            if not self.__is_extruding and self.__extrude_signal != 0:
                lines.append(f'SIGNAL {self.__extrude_signal}\n')
                self.__is_extruding = True

        elif self.__is_extruding:
            lines.append(f'SIGNAL -{self.__extrude_signal}\n')
            self.__is_extruding = False

            # add retraction if enabled
            if self.__retract_signal != 0:
                lines.append(
                    f'PULSE {self.__retract_signal}, 0.1'
                )

        # xyz positions
        # simplification of path is only possible if the line has the same z coordinate
        if z_pos is None or z_pos == self.__z_pos:
            delta_x = self.__x_pos - x_pos if x_pos is not None else 0
            delta_y = self.__y_pos - y_pos if y_pos is not None else 0

            xy_delta = math.sqrt(delta_x ** 2 + delta_y ** 2)

            # check if the delta is smaller than the specified minimum distance
            if xy_delta <= self.__execute_options.min_distance:
                # check if the already skipped distance is smaller than the minimum distance
                if self.__skipped_distance < self.__execute_options.min_distance:
                    self.__skipped_distance += xy_delta
                    self.__skipped_moves += 1
                    return lines

                # if not, append the move and reset the counter
                else:
                    self.__skipped_distance = 0

        # append the xyz move
        self.__x_pos = x_pos if x_pos is not None else self.__x_pos
        self.__y_pos = y_pos if y_pos is not None else self.__y_pos
        self.__z_pos = z_pos if z_pos is not None else self.__z_pos

        move_command = f'LMOVE SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos})'

        if line.comment:
            move_command += f' ;{line.command}'

        move_command += '\n'

        lines.append(move_command)

        return lines
