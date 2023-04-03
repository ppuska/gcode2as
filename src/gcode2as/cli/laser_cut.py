import math
from typing import List, Optional, Tuple
from click import echo
from colorama import Back, Style

from gcodeparser.gcode_parser import GcodeLine
import inquirer
from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.utils.validation import validate_is_int
from gcode2as.converter import Converter


class LaserCut(CLICommand):

    def __init__(self) -> None:
        self.__x_pos = 0
        self.__y_pos = 0
        self.__z_pos = 0

        self.__laser_on_signal: int = 0
        self.__laser_off_signal: Optional[int] = None
        self.__is_laser_on = False

        self.__skipped_distance = 0
        self.__skipped_moves = 0

        self.__execute_options: Optional[CLICommandOptions] = None

    @property
    def message(self) -> str:
        return "Laser cutting"

    def execute(self, options: CLICommandOptions) -> List[str] | None:
        self.__execute_options = options

        laser_control_type_key = 'laser_control_type'
        one_signal_key = 'One signal'
        two_signal_key = 'Two signals'
        
        vase_mode_key = 'vase_mode'
        laser_control_signal_first_key = 'laser_control_first_signal'
        laser_control_signal_second_key = 'laser_control_second_signal'

        questions = [
            inquirer.List(
                laser_control_type_key,
                message='How is the laser controlled?',
                choices=[one_signal_key, two_signal_key]
            ),
            inquirer.Text(
                laser_control_signal_first_key,
                message='Enter the signal number to turn on the laser',
                validate=validate_is_int
            ),
            inquirer.Text(
                laser_control_signal_second_key,
                message='Enter the signal number to turn off the laser',
                validate=validate_is_int,
                ignore=lambda answers: answers[laser_control_type_key] == one_signal_key
            )
        ]

        answers = inquirer.prompt(questions)

        if answers is None:
            return

        self.__laser_on_signal = int(answers[laser_control_signal_first_key])
        laser_off_string = answers.get(laser_control_signal_second_key)

        if laser_off_string is None:
            self.__laser_off_signal = None

        else:
            self.__laser_off_signal = int(laser_off_string)

        converter = Converter(options.file)

        lines = converter.convert(self.__process_line)

        echo(f'Conversion {Back.GREEN}done{Style.RESET_ALL}.')
        echo(f'{Back.CYAN}Stats:{Style.RESET_ALL}')
        echo(f'\tGCODE file had {converter.file_length} lines')
        echo(f'\tOmitted {self.__skipped_moves} lines')
        echo(f'\tAS file length is {len(lines)} lines')

        return lines

    def __process_line(self, line: GcodeLine):

        processed_lines: List[str] = []

        # check for parameters
        feed = line.params.get('F')
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
        if line.params.get('F') is not None:
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

        if self.__is_laser_on:
            if self.__laser_off_signal is None:
                # one signal laser control
                lines.append(f'SIGNAL -{self.__laser_on_signal}')

            else:
                # two signal laser control
                lines.append(f'PULSE -{self.__laser_off_signal}')

        return lines

    def __process_g1(
            self,
            line: GcodeLine,
            feed: float | None,
            position: Tuple[float | None, float | None, float | None]
    ):
        lines = []

        x_pos, y_pos, z_pos = position

        # feed
        if feed is not None:
            # append the command
            lines.append(f'SPEED {feed} MM/MIN ALWAYS\n')

        # laser control
        if not self.__is_laser_on:
            if self.__laser_off_signal is None:
                # one signal laser control
                lines.append(f'SIGNAL {self.__laser_on_signal}')

            else:
                # two signal laser control
                lines.append(f'PULSE {self.__laser_on_signal}')

            self.__is_laser_on = True

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
