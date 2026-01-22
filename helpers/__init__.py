import enum
import functools
import warnings
from typing import Callable

import babel.numbers
from gettext import pgettext

import wx

from helpers.observables import Observable


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


def wx_call_after_debounce(*observables: Observable, callback: Callable, wait_time: float = 0.4):
    waiting = False

    def _debounced(*args, **kwargs):
        nonlocal waiting
        if not waiting:
            waiting = True

            def call_and_reset():
                nonlocal waiting
                callback(*args, **kwargs)
                waiting = False

            wx.CallAfter(call_and_reset)

    for obs in observables:
        setattr(obs, '_debounce_callback', _debounced)
        obs.subscribe(_debounced)