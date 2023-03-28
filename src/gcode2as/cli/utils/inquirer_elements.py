import inquirer

from gcode2as.cli.utils.validation import validate_is_float

OVERRIDE_SPEED_KEY = 'override_speed'
OVERRIDE_SPEED_VALUE_KEY = 'override_speed_value'


def ask_override_speed():
    """Returns a sequence of questions to ask the user if they want to override the printing speed"""
    return [
        inquirer.Confirm(
            OVERRIDE_SPEED_KEY,
            message='Would you like to override the speed? This creates a constant speed profile',
            default=False
        ),
        inquirer.Text(
            OVERRIDE_SPEED_VALUE_KEY,
            message="Enter the new speed",
            validate=validate_is_float,
            ignore=lambda answers: not answers[OVERRIDE_SPEED_KEY]
        )
    ]
