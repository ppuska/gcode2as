from io import TextIOWrapper
from typing import Dict, List

from click import echo
import inquirer
from inquirer.errors import ValidationError
from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.converter import convert_to_as
from gcode2as.model.line import Line


class FDM(CLICommand):

    DEFAULT_EXTRUDE_SIGNAL = 2001
    DEFAULT_RETRACT_SIGNAL = 2002

    @staticmethod
    def __validate_is_float(_, current: str):
        try:
            float(current)

        except ValueError:
            raise ValidationError('', reason='Input must be a float')

        return True

    @staticmethod
    def __validate_is_int(_, current: str):
        try:
            int(current)

        except ValueError:
            raise ValidationError('', reason='Input must be integer')

        return True

    @property
    def message(self) -> str:
        return "FDM 3D Printing"

    def execute(self, options: CLICommandOptions):
        # keys for the inquirer
        extrude_key = 'extrude'
        retract_key = 'retract'
        override_speed_key = 'override_speed'
        override_speed_value_key = 'override_speed_value'

        questions = [
            inquirer.Text(
                extrude_key,
                message='Specify the extrude signal',
                default=FDM.DEFAULT_EXTRUDE_SIGNAL
            ),
            inquirer.Text(
                retract_key,
                message='Specify the retract signal',
                default=FDM.DEFAULT_RETRACT_SIGNAL
            ),
            inquirer.Confirm(
                override_speed_key,
                message='Would you like to override the speed? This creates a constant speed profile',
                default=False
            ),
            inquirer.Text(
                override_speed_value_key,
                message="Enter the new speed",
                validate=FDM.__validate_is_float,
                ignore=lambda answers: not answers[override_speed_key]
            )
        ]

        answers: Dict[str, str] | None = inquirer.prompt(questions)

        if answers is None:
            return

        extrude_signal = int(answers[extrude_key])
        retract_signal = int(answers[retract_key])

        override_speed = answers.get(override_speed_value_key)

        return self.__process(
            options,
            extrude_signal,
            retract_signal,
            override_speed
        )

    def __create_line_generator(self, file: TextIOWrapper):
        """Creates a generator object to generate lines from the read file"""
        for line in file:
            yield line

    def __process(
            self,
            options: CLICommandOptions,
            extrude: int,
            retract: int,
            override_speed: str | None
    ) -> List[str]:
        line_generator = self.__create_line_generator(options.file)

        echo(f"Extrude signal set to {extrude}")
        echo(f"Retract signal set to {retract}")
        if override_speed is not None:
            echo(f"Speed is overridden to {override_speed}")
            override_speed = int(override_speed)

        lines = []

        for i, line in enumerate(line_generator):
            if i == 0:
                lines.append(Line.parse(line))
            else:
                lines.append(Line.parse(line, lines[i - 1]))

        lines_as = convert_to_as(
            lines,
            extrude,
            retract,
            options.min_distance,
            override_speed,
            options.verbose
        )

        return lines_as
