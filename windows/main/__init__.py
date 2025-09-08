import wx

from helpers.observables import Observable, ObservableArray
from models.database import Database, Table, Column
from models.session import Session

SESSIONS: ObservableArray[Session] = ObservableArray()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_DATABASE: Observable[Database] = Observable()
CURRENT_TABLE: Observable[Table] = Observable()
CURRENT_COLUMN: Observable[Column] = Observable()
