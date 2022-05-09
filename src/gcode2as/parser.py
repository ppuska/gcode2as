from line import Line

def parse(line: str) -> Line:
    """Parses a single line of G-Code"""

    result = Line()

    for word in line.split(" "):
        print(word)