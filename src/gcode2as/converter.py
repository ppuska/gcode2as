"""Module for converting Line objects to AS code"""

from typing import List
from math import sqrt

from progress.bar import IncrementalBar

from .model.line import Line


def convert_to_as(
    lines: List[Line],
    extrude_signal: int,
    retract_signal: int,
    min_dist: float,
    override_speed: int | None = None,
    debug: bool = False,
) -> List[str]:
    """Converts the given list of line objects to a list of as commands

    Args:
        lines (List[Line]): The list of line objects to convert
        extrude_signal (int): The signal number of the extrusion signal
        retract_signal (int): The signal number of the retraction signal
        min_dist (float): The minimum distance parameter
        debug (bool, optional): If true, additional information will be generated
        during the conversion. Defaults to False.

    Returns:
        List[str]: A list of strings formatted to AS commands
    """

    is_extruding = False
    is_retracting = False

    speed = 0
    extrude = 0

    as_str = []

    prev_line = None
    omitted_lines_num = 0
    kept_lines_num = 0
    distance_skipped = 0

    progress_bar = IncrementalBar("Converting", max=len(lines))

    for line in lines:

        progress_bar.next()

        dist_to_previous = 0

        if not line.valid:
            if line.comment:
                as_str.append(f"; {line.comment}\n")
            else:
                as_str.append(f";{line.raw}\n")
            continue

        # override speed value if necessary
        if override_speed is not None:
            if speed != override_speed:
                as_str.append(f"SPEED {override_speed} MM/MIN ALWAYS\n")
                speed = override_speed

        # detect speed change
        elif speed != line.f_prop and line.f_prop is not None:
            as_str.append(f"SPEED {line.f_prop} MM/MIN ALWAYS\n")
            speed = line.f_prop

        # process extrusion logic
        if line.e_prop is not None:

            # e increase is extrusion
            if extrude < line.e_prop and not is_extruding:
                add_extrude(as_str, extrude_signal)
                is_extruding = True
                extrude = line.e_prop

            # e decrease is retraction
            elif extrude > line.e_prop and not is_retracting:
                if is_extruding:
                    add_extrude(as_str, False)

                add_retract(as_str, retract_signal)
                is_retracting = True

            elif extrude == line.e_prop:
                if is_extruding:
                    add_extrude(as_str, extrude_signal, False)
                    is_extruding = False
                    is_retracting = False

        elif is_extruding:
            add_extrude(as_str, extrude_signal, False)
            is_extruding = False
            is_retracting = False

        # check if the distance is under the minimum distance
        if prev_line is not None and prev_line.z_prop == line.z_prop:
            # calculate the distance from the previous point
            dist_to_previous = sqrt(
                (prev_line.x_prop - line.x_prop) ** 2
                + (prev_line.y_prop - line.y_prop) ** 2
            )

            if dist_to_previous + distance_skipped < min_dist:
                distance_skipped += dist_to_previous
                omitted_lines_num += 1
                continue

        distance_skipped = 0

        as_str.append(line.to_as_command(debug=debug))
        prev_line = line
        kept_lines_num += 1

    print("\r", end="")  # delete progressbar
    print(
        f"Processed {len(lines)} lines, \
        omitted {omitted_lines_num} lines, \
        commands converted to AS: {kept_lines_num}, \
        length of AS file: {len(as_str)}"
    )

    return as_str


def add_extrude(where: List[str], signal: int, enable: bool = True):
    """Adds a signal command to start or stop extrusion

    Args:
        where (List[str]): The list of commands to add the command to
        signal (int): The number of the extrusion signal
        enable (bool, optional): If true extrusion will be enabled, otherwise disabled.
        Defaults to True.
    """
    where.append(f'SIGNAL {"" if enable else "-"}{signal}\n')


def add_retract(where: List[str], signal: int):
    """Adds a pulse command to initiate retraction into the generated commands

    Args:
        where (List[str]): The list of commands to add the command into
        signal (int): The number of the retraction signal
    """
    where.append(f"PULSE {signal}, 0.1\n")
