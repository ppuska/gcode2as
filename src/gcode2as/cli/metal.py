
import math
from typing import List, Optional, Tuple
from click import echo
from colorama import Back, Fore, Style
import inquirer
from gcodeparser.gcode_parser import GcodeLine

from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.utils.validation import validate_is_float
from gcode2as.converter import Converter


class Metal(CLICommand):

    def __init__(self) -> None:
        self.__x_pos = 0
        self.__y_pos = 0
        self.__z_pos = 0

        self.__welding_speed: float | None = None

        self.__skipped_distance = 0
        self.__skipped_moves = 0
        self.__lines_comment = 0

        self.__last_g0: Optional[GcodeLine] = None
        self.__weld: List[GcodeLine] = []

        self.__is_using_vase_mode = False
        self.__is_inverted = False

        self.__execute_options: CLICommandOptions = None

    @property
    def message(self) -> str:
        return "Metal 3D Printing"

    def execute(self, options: CLICommandOptions):
        self.__execute_options = options
        echo(f'[{Fore.YELLOW}Warning{Fore.RESET}]: The generated code will only work with robots that have a welding card installed.')

        speed_key = 'speed'
        vase_mode_key = 'vase mode'
        inverted_key = 'inverted'

        questions = [
            inquirer.Confirm(
                vase_mode_key,
                message="Is the model sliced in vase mode (spiralise outer contours)?",
            ),
            inquirer.Text(
                speed_key,
                message='Set the welding speed',
                validate=validate_is_float,
                default=15
            ),
            inquirer.Confirm(
                inverted_key,
                message="Is the model inverted (upside down)?",
                default=False,
            )
        ]

        answers = inquirer.prompt(questions)

        if answers is None:
            return

        speed = answers[speed_key]

        self.__is_using_vase_mode = answers[vase_mode_key]

        self.__is_inverted = answers[inverted_key]

        self.__welding_speed = float(speed)

        converter = Converter(options.file)

        lines = []

        # set the welding conditions
        lines.append(
            converter.format_to_as_line_comment(
                "WELDING CONDITIONS",
                pad=True
            )
        )
        lines.append(f'W1SET 1 = {self.__welding_speed}, 1, 1, 0, 0\n')
        lines.append(f'W2SET 1 = 0.1, 1, 1\n')
        lines.append(
            converter.format_to_as_line_comment('', pad=True)
        )

        try:
            lines.extend(
                converter.convert(self.__process_line)
            )

        except ValueError as error:
            echo(error)

            if options.verbose:
                if self.__weld:
                    echo(f'Weld move list: ')
                    [echo(f'\t{weld}') for weld in self.__weld]

                if self.__last_g0:
                    echo(f'Stored G0: {self.__last_g0}')

            echo(
                f'{Back.YELLOW}The file will only be generated partially.{Style.RESET_ALL}')
            return lines

        # flush the last weld instruction
        if self.__weld:
            lines.extend(self.__process_weld())

        echo(f'[{Fore.BLUE}Info{Fore.RESET}]: Model converted. Stats:')
        echo(
            f'\t{Fore.LIGHTBLACK_EX}GCode lines: {converter.file_length} -> AS lines: {len(lines)}'
        )
        echo(f'\tOmitted lines: {self.__skipped_moves}')
        echo(
            f'\tThe code contains {self.__lines_comment} comments, which is {self.__lines_comment / len(lines) * 100}% of the file{Style.RESET_ALL}'
        )

        return lines

    def __process_line(self, line: GcodeLine) -> Optional[List[str]]:
        """Gets called on each GcodeLine object to convert it to a list of strings"""
        processed_lines: List[str] = []

        # process comment-only lines
        if line.command[0] == ';':
            processed_lines.append(f'; {line.comment}')
            self.__lines_comment += 1

        # G0 move
        elif line.command[0] == 'G' and line.command[1] == 0:

            # if the weld line has to be ended
            if self.__weld:
                processed_lines.extend(self.__process_weld())

            # if this comes after a G0 then process the last one
            elif self.__last_g0 is not None:
                processed_lines.extend(
                    self.__process_g0(self.__last_g0)
                )

            self.__last_g0 = line

        # G1 move
        elif line.command[0] == 'G' and line.command[1] == 1:
            self.__process_g1(line)

        return processed_lines

    def __process_g0(self, line: GcodeLine, weld_start: bool = False):
        """Processes a single line of G0 code instruction"""
        lines = []

        feed, position = Metal.get_line_params(line)

        x_pos, y_pos, z_pos = position

        if self.__is_inverted and z_pos is not None:
            z_pos = -z_pos

        # xyz positions
        self.__x_pos = x_pos if x_pos is not None else self.__x_pos
        self.__y_pos = y_pos if y_pos is not None else self.__y_pos
        self.__z_pos = z_pos if z_pos is not None else self.__z_pos

        if weld_start:
            move_command = f'LWS SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos})'

        else:
            # feed
            if feed is not None and self.__welding_speed is None:
                # append the command
                lines.append(f'SPEED {feed} MM/MIN ALWAYS')

            move_command = f'LMOVE SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos})'

        if line.comment:
            move_command += f' ;{line.command}'

        if self.__execute_options.verbose:
            move_command += f' ;{line.gcode_str}'

        move_command += '\n'

        lines.append(move_command)

        return lines

    def __process_g1(self, line: GcodeLine):
        """Processes a single line of G1 G-code command"""

        _, position = Metal.get_line_params(line)

        x_pos, y_pos, z_pos = position

        if x_pos is None and y_pos is None and z_pos is None:
            # irrelevant command
            return ""

        self.__weld.append(line)

        # xyz positions
        self.__x_pos = x_pos if x_pos is not None else self.__x_pos
        self.__y_pos = y_pos if y_pos is not None else self.__y_pos
        self.__z_pos = z_pos if z_pos is not None else self.__z_pos

        return ""

    def __process_weld(self):
        lines = []

        if not self.__weld or self.__last_g0 is None:
            raise ValueError(
                f'{Back.RED}Invalid State{Style.RESET_ALL}: Weld move list or the last G0 move cannot be empty'
            )

        # process the weld start point
        lines.extend(
            self.__process_g0(self.__last_g0, weld_start=True)
        )
        self.__last_g0 = None

        for weld in self.__weld:
            _, position = Metal.get_line_params(weld)

            x_pos, y_pos, z_pos = position

            # check if the model is inverted
            if self.__is_inverted and z_pos is not None:
                z_pos = -z_pos

            skip_move = self.__check_if_move_skip(x_pos, y_pos, z_pos)

            self.__x_pos = x_pos if x_pos is not None else self.__x_pos
            self.__y_pos = y_pos if y_pos is not None else self.__y_pos
            self.__z_pos = z_pos if z_pos is not None else self.__z_pos

            move_command = ''

            if weld == self.__weld[-1]:
                # process the last weld

                move_command = f'LWE SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos}), 1, 1'

                if self.__execute_options.verbose:
                    move_command += f' ;{weld.gcode_str}'

            elif skip_move:
                continue

            else:

                move_command = f'LWC SHIFT(a BY {self.__x_pos}, {self.__y_pos}, {self.__z_pos}), 1'

                if weld.comment:
                    move_command += f' ;{weld.command}'

                if self.__execute_options.verbose:
                    move_command += f' ;{weld.gcode_str} dist: {self.__skipped_distance}'

            if move_command:
                move_command += '\n'

            lines.append(move_command)

        self.__weld = []

        return lines

    def __check_if_move_skip(self, x_pos: Optional[float], y_pos: Optional[float], z_pos: Optional[float]) -> bool:
        # the move can only be skipped if the z coordinate matches or we are using vase mode
        abs_delta = 0

        if not self.__is_using_vase_mode:
            if z_pos is None or z_pos == self.__z_pos:
                delta_x = self.__x_pos - x_pos if x_pos is not None else 0
                delta_y = self.__y_pos - y_pos if y_pos is not None else 0

                abs_delta = math.sqrt(delta_x ** 2 + delta_y ** 2)

        else:
            delta_x = self.__x_pos - x_pos if x_pos is not None else 0
            delta_y = self.__y_pos - y_pos if y_pos is not None else 0
            delta_z = self.__z_pos - z_pos if z_pos is not None else 0

            abs_delta = math.sqrt(delta_x ** 2 + delta_y ** 2 + delta_z ** 2)

        # check if the delta is smaller than the specified minimum distance
        if abs_delta <= self.__execute_options.min_distance:
            self.__skipped_distance += abs_delta
            # check if the already skipped distance is smaller than the minimum distance
            if self.__skipped_distance < self.__execute_options.min_distance:
                self.__skipped_moves += 1
                return True

            # if not, append the move and reset the counter
            else:
                self.__skipped_distance = 0

        return False

    @staticmethod
    def get_line_params(line: GcodeLine) -> Tuple[float | None, Tuple[float | None, float | None, float | None]]:
        feed = line.params.get('F')
        position = (
            line.params.get('X'),
            line.params.get('Y'),
            line.params.get('Z'),
        )

        return feed, position
