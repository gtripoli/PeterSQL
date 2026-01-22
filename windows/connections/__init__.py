from helpers.observables import Observable
from structures.connection import Connection, ConnectionDirectory

CURRENT_DIRECTORY: Observable[ConnectionDirectory] = Observable()
CURRENT_CONNECTION: Observable[Connection] = Observable()
PENDING_CONNECTION: Observable[Connection] = Observable()


def wx_colour_to_hex(col):
    return f"#{col.Red():02x}{col.Green():02x}{col.Blue():02x}"
