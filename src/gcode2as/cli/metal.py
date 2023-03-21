from io import TextIOWrapper

from click import echo
from colorama import Back, Style
from gcode2as.cli import CLICommand, CLICommandOptions


class Metal(CLICommand):
    @property
    def message(self) -> str:
        return "Metal 3D Printing"

    def execute(self, options: CLICommandOptions):
        return echo(f"{Back.RED}Sorry not implemented yet{Style.RESET_ALL}")
