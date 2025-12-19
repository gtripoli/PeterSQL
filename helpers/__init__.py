import enum
import babel.numbers
from gettext import pgettext


class SizeUnit(enum.Enum):
    BYTE = pgettext("unit", "B")
    KILOBYTE = pgettext("unit", "KB")
    MEGABYTE = pgettext("unit", "MB")
    GIGABYTE = pgettext("unit", "GB")
    TERABYTE = pgettext("unit", "TB")


def bytes_to_human(bytes: float, locale: str = "en_US") -> str:
    units = [
        SizeUnit.BYTE,
        SizeUnit.KILOBYTE,
        SizeUnit.MEGABYTE,
        SizeUnit.GIGABYTE,
        SizeUnit.TERABYTE,
    ]
    index = 0
    while bytes >= 1024 and index < len(units) - 1:
        index += 1
        bytes /= 1024.0

    formatted_number = babel.numbers.format_decimal(bytes, locale=locale)
    return f"{formatted_number} {units[index].value}"
