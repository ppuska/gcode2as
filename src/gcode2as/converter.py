import logging
import math

from src.gcode2as.line import Line


class Converter:
    """This is a class for converting parsed G-Code lines to Kawasaki AS lines"""

    def __init__(self, program_name: str,
                 output_file_path: str,
                 extrude_signal: int = 0,
                 section_size: int = 1000,
                 min_dist: float = 2.0
                 ):
        # store the program name
        self.__program_name = program_name

        # create a file for the program steps
        self.__file = open(f"{output_file_path}/{program_name}.pg", 'w')

        # create a 'header' file that contains all the subroutine calls
        self.__header_file = open(f"{output_file_path}/{program_name}_header.pg", 'w')

        self.__is_first_line = True

        # create a variable to hold the previous moves geometry
        self.__prev_move = {}

        # extrusion signal
        self.__extrude_signal = extrude_signal

        # statistics
        self.__lines_loaded = 0
        self.__lines_converted = 0
        self.__lines_omitted = 0
        self.__lines_invalid = 0

        # sectioning
        self.__section_number = 0
        self.__section_size = section_size

        # minimum travel distance
        self.__min_dist = min_dist

    def convert_parsed_line(self, line: Line):

        self.__lines_loaded += 1

        # check if this is the first line in the file
        if self.__is_first_line:
            self.__file.write(f".PROGRAM {self.__program_name}()\n")
            self.__is_first_line = False

        line_invalid = False

        as_str = "\t"  # indent the line

        line_x = line.geometry.get(line.X)
        line_y = line.geometry.get(line.Y)
        line_z = line.geometry.get(line.Z)

        prev_x = self.__prev_move.get(line.X)
        prev_y = self.__prev_move.get(line.Y)
        prev_z = self.__prev_move.get(line.Z)

        # calculate the distance to the previous point
        try:
            x_x_2 = (line_x - prev_x) ** 2
            y_y_2 = (line_y - prev_y) ** 2

        except TypeError:
            logging.debug("No previous move")

        else:
            if math.sqrt(x_x_2 + y_y_2) < self.__min_dist:
                self.__lines_omitted += 1
                return

        # region speed

        if line.feed != self.__prev_move.get(Line.F):
            as_str += f"SPEED {line.feed}\n\t"
            self.__prev_move[line.F] = line.feed  # set the new value

        # endregion

        # region extrusion

        if line.extrude and self.__prev_move.get(line.E) is None:
            as_str += f"SIGNAL {self.__extrude_signal}\n\t"
            self.__prev_move[line.E] = line.extrude  # set the new value

        if not line.extrude and self.__prev_move.get(line.E) is not None:
            as_str += f"SIGNAL -{self.__extrude_signal}\n\t"
            self.__prev_move.pop(line.E)  # remove the Extrusion value

        # endregion

        # region linear move

        as_str += "LMOVE SHIFT(a BY "

        if line_x is not None:
            as_str += f"{line_x}, "
            self.__prev_move[line.X] = line_x

        elif self.__prev_move.get(line.X) is not None:
            as_str += str(self.__prev_move.get(line.X))

        else:
            line_invalid = True

        if line_y is not None:
            as_str += f"{line_y}, "
            self.__prev_move[line.Y] = line_y

        elif self.__prev_move.get(line.Y) is not None:
            as_str += str(self.__prev_move.get(line.Y))

        else:
            line_invalid = True

        if line_z is not None:
            as_str += f"{line_z}, "
            self.__prev_move[line.Z] = line_z

        elif self.__prev_move.get(line.Z) is not None:
            as_str += str(self.__prev_move.get(line.Z))

        else:
            line_invalid = True

        as_str = as_str[:-2] + ")\n"

        # endregion

        if line_invalid:
            logging.debug("Invalid line")
            self.__lines_invalid += 1

        else:
            self.__file.write(as_str)
            self.__lines_converted += 1

    def close(self):
        self.__file.write(".END")

        self.__file.close()
        self.__header_file.close()

        logging.info("Conversion done")
        logging.info("Loaded lines: %x", self.__lines_loaded)
        logging.info("Omitted lines: %x", self.__lines_omitted)
        logging.info("Invalid lines: %x", self.__lines_invalid)
        logging.info("Converted lines: %x", self.__lines_converted)




