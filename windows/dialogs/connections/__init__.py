from helpers.observables import Observable
from structures.connection import Connection, ConnectionDirectory

CURRENT_DIRECTORY: Observable[ConnectionDirectory] = Observable()
CURRENT_CONNECTION: Observable[Connection] = Observable()
PENDING_CONNECTION: Observable[Connection] = Observable()

