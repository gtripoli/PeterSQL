import enum
import os
import sys

from typing import Callable
from pathlib import Path
from gettext import pgettext

import wx
import babel.numbers

from helpers.observables import Observable


class SizeUnit(enum.Enum):
    BYTE = pgettext("unit", "B")
    KILOBYTE = pgettext("unit", "KB")
    MEGABYTE = pgettext("unit", "MB")
    GIGABYTE = pgettext("unit", "GB")
    TERABYTE = pgettext("unit", "TB")


def wx_colour_to_hex(colour):
    if isinstance(colour, str):
        if colour.startswith('#'):
            return colour
        return f"#{colour}"
    return f"#{colour.Red():02x}{colour.Green():02x}{colour.Blue():02x}"


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


def get_base_path(base_path: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return base_path


def get_resource_path(base_path: Path, *paths: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*paths)

    return get_base_path(base_path).joinpath(*paths)


def get_config_dir() -> Path:
    base: str = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / "petersql"


def get_data_dir() -> Path:
    base: str = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "petersql"


def get_cache_dir() -> Path:
    base: str = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    return Path(base) / "petersql"