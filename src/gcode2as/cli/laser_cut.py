from typing import List

import inquirer
from gcode2as.cli import CLICommand, CLICommandOptions
from gcode2as.cli.utils import inquirer_elements
from gcode2as.formatter import create_line_generator


class LaserCut(CLICommand):
    @property
    def message(self) -> str:
        return "Laser cutting"

    def execute(self, options: CLICommandOptions) -> List[str] | None:
        answers = inquirer.prompt(
            inquirer_elements.ask_override_speed()
        )

        if answers is None:
            return

        override_speed = answers.get(
            inquirer_elements.OVERRIDE_SPEED_VALUE_KEY
        )

        line_generator = create_line_generator(options.file)

        return
