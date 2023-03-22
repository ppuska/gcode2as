from inquirer.errors import ValidationError


def validate_is_float(_, current: str):
    try:
        float(current)

    except ValueError:
        raise ValidationError('', reason='Input must be a float')

    return True


def validate_is_int(_, current: str):
    try:
        int(current)

    except ValueError:
        raise ValidationError('', reason='Input must be integer')

    return True
