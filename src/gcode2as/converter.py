import logging
import math

from gcode2as.line import Line


class Converter:
    """This is a class for converting parsed G-Code lines to Kawasaki AS lines"""

    def __init__(self, program_name: str,
                 output_file_path: str,
                 extrude_signal: int = 0,
                 section_size: int = 1000,
                 min_dist: float = 2.0,
                 debug: bool = False
                 ):
        # store the program name
        self.__program_name = program_name

        # create a file for the program steps
        self.__file = open(f"{output_file_path}/{program_name}.pg", 'w')

        # create a 'header' file that contains all the subroutine calls
        self.__header_file = open(f"{output_file_path}/{program_name}_header.pg", 'w')

        self.__is_first_line = True

        # create a variable to hold the previous moves geometry
        self.__prev_move = { Line.X: 0.0, Line.Y: 0.0, Line.Z: 0.0 }

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
        self.__section_current_size = 0

        # minimum travel distance
        self.__min_dist = min_dist

        # debug mode
        self.__debug = debug

    def convert_parsed_line(self, line: Line):

        self.__lines_loaded += 1

        # check if the line is comment
        if line.is_comment:
            self.__lines_invalid += 1
            return

        # check if we need to begin a new section
        if self.__section_current_size >= self.__section_size:
            # program end script
            self.__file.write(".END\n\n")
            self.__section_number += 1
            self.__section_current_size = 0 # reset the section size
            self.__is_first_line = True

        # check if this is the first line in the file
        if self.__is_first_line:
            self.__file.write(f".PROGRAM {self.__program_name}_{self.__section_number}()\n")
            self.__is_first_line = False

        line_invalid = False

        as_str = ""

        line_x = line.geometry.get(line.X)
        line_y = line.geometry.get(line.Y)
        line_z = line.geometry.get(line.Z)

        prev_x = self.__prev_move.get(line.X)
        prev_y = self.__prev_move.get(line.Y)

        # region speed

        if line.feed != self.__prev_move.get(Line.F) and line.feed > 0.0:
            as_str += f"\tSPEED {line.feed} MM/S ALWAYS\n"
            self.__prev_move[line.F] = line.feed  # set the new value

        # endregion

        # region extrusion

        if line.extrude and self.__prev_move.get(line.E) is None:
            as_str += f"\tSIGNAL {self.__extrude_signal}\n"
            self.__prev_move[line.E] = line.extrude  # set the new value

        if not line.extrude and self.__prev_move.get(line.E) is not None:
            as_str += f"\tSIGNAL -{self.__extrude_signal}\n"
            self.__prev_move.pop(line.E)  # remove the Extrusion value

        # endregion

        # calculate the distance to the previous point
        try:
            x_x_2 = (line_x - prev_x) ** 2
            y_y_2 = (line_y - prev_y) ** 2

        except TypeError:
            pass

        else:
            if math.sqrt(x_x_2 + y_y_2) < self.__min_dist:
                self.__lines_omitted += 1
                self.__file.write(as_str)
                self.__section_current_size += as_str.count('\n')
                return

        # check if its a zero length move
        if line.zero_move:
            self.__lines_omitted += 1
            return

        # region linear move

        as_str += "\tLMOVE SHIFT(a BY "

        if line_x is not None:
            as_str += f"{line_x}, "
            self.__prev_move[line.X] = line_x

        elif self.__prev_move.get(line.X) is not None:
            as_str += f"{self.__prev_move.get(line.X)}, "

        else:
            line_invalid = True

        if line_y is not None:
            as_str += f"{line_y}, "
            self.__prev_move[line.Y] = line_y

        elif self.__prev_move.get(line.Y) is not None:
            as_str += f"{self.__prev_move.get(line.Y)}, "

        else:
            line_invalid = True

        if line_z is not None:
            as_str += f"{line_z}, "
            self.__prev_move[line.Z] = line_z

        elif self.__prev_move.get(line.Z) is not None:
            as_str += f"{self.__prev_move.get(line.Z)}, "

        else:
            line_invalid = True

        as_str = as_str[:-2] + ")"

        if self.__debug:
            as_str += f" ;{line.raw}\n"

        else:
            as_str += " \n"

        # endregion

        if line_invalid:
            logging.debug(f"Invalid line: {line.raw}")
            self.__lines_invalid += 1

        else:
            self.__file.write(as_str)
            self.__lines_converted += 1
            self.__section_current_size += as_str.count('\n')

    def close(self):
        # close file
        self.__file.write(".END\n")
        self.__file.close()

        # generate header file
        if self.__section_number > 0:
            self.__header_file.write(f".PROGRAM {self.__program_name}()\n")
            for i in range(self.__section_number):
                self.__header_file.write(f"\tCALL {self.__program_name}_{i}\n")

            self.__header_file.write(".END\n")

        # close the header file
        self.__header_file.close()

        logging.info("Conversion done")
        logging.info("Loaded lines: %i", self.__lines_loaded)
        logging.info("Omitted lines: %i", self.__lines_omitted)
        logging.info("Invalid lines: %i", self.__lines_invalid)
        logging.info("Converted lines: %i", self.__lines_converted)

        logging.info(f"Program saved to {self.__file.name}")
        if self.__section_number > 0:
            logging.info(f"Header file saved as {self.__header_file.name}")




