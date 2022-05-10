from .line import Line


def parse(line: str) -> Line:
    """Parses a single line of G-Code"""

    result = Line()

    result.raw = line[:-1]

    if line.startswith(";"):
        result.is_comment = True

    for word in line.split(" "):
        if word.startswith(";"):
            # comment break out of the loop
            break

        if word == Line.G0:
            result.move_type = Line.G0

        elif word == Line.G1:
            result.move_type = Line.G1

        elif word.startswith(Line.X) or word.startswith(Line.Y) or word.startswith(Line.Z):
            result.geometry[word[0]] = float(word[1:])

        elif word.startswith(Line.F):
            result.feed = float(word[1:])

        elif word.startswith(Line.E):
            result.extrude = float(word[1:])

    return result
