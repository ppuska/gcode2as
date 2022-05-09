import logging

from src.gcode2as.line import Line


class Converter:
    """This is a class for converting parsed G-Code lines to Kawasaki AS lines"""

    def __init__(self, program_name: str, output_file_path: str, extrude_signal: int = 0, section_size: int = 1000):
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
        self.__lines_parsed = 0
        self.__lines_omitted = 0
        self.__lines_invalid = 0

        # sectioning
        self.__section_number = 0
        self.__section_size = section_size

    def convert_parsed_line(self, line: Line):

        # check if this is the first line in the file
        if self.__is_first_line:
            self.__file.write(f".PROGRAM {self.__program_name}()\n")
            self.__is_first_line = False

        line_invalid = False

        as_str = "\t"  # indent the line

        line_x = line.geometry.get(line.X)
        line_y = line.geometry.get(line.Y)
        line_z = line.geometry.get(line.Z)

        # region extrusion

        if line.extrude and self.__prev_move.get(line.E) is None:
            as_str += f"SIGNAL {self.__extrude_signal}\n\t"
            self.__prev_move[line.E] = line.extrude  # set the new value

        if not line.extrude and self.__prev_move.get(line.E) is not None:
            as_str += f"SIGNAL -{self.__extrude_signal}\n\t"
            self.__prev_move.pop(line.E)  # remove the Extrusion value

        # endregion

        as_str += "LMOVE SHIFT(a BY "

        if line_x is not None:
            as_str += f"{line_x}, "

        elif self.__prev_move.get(line.X) is not None:
            as_str += str(self.__prev_move.get(line.X))

        else:
            line_invalid = True

        if line_y is not None:
            as_str += f"{line_y}, "

        elif self.__prev_move.get(line.Y) is not None:
            as_str += str(self.__prev_move.get(line.Y))

        else:
            line_invalid = True

        if line_z is not None:
            as_str += f"{line_z}, "

        elif self.__prev_move.get(line.Z) is not None:
            as_str += str(self.__prev_move.get(line.Z))

        else:
            line_invalid = True

        as_str = as_str[:-2] + ")\n"

        if line_invalid:
            logging.debug("Invalid line")

        else:
            self.__file.write(as_str)

    def close(self):
        self.__file.write(".END")

        self.__file.close()
        self.__header_file.close()




