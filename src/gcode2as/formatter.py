from math import ceil
from typing import List

MAX_PROGRAM_LENGTH = 1000


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
            lines[i * MAX_PROGRAM_LENGTH: (i + 1) * MAX_PROGRAM_LENGTH]
        )
        as_program += ".END\n\n"

    as_program += f".PROGRAM {program_name}\n"
    for i in range(subprogram_number):
        as_program += f"CALL {program_name}_{i}\n"

    as_program += ".END\n"

    return as_program
