import wx

from helpers.observables import Observable, ObservableArray
from models.database import Database, Table, Column
from models.session import Session

SESSIONS: ObservableArray[Session] = ObservableArray()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_DATABASE: Observable[Database] = Observable()
CURRENT_TABLE: Observable[Table] = Observable()
CURRENT_COLUMN: Observable[Column] = Observable()

class CursorWait():
    CURSOR_WAIT = Observable()

    def __init__(self):
        self.CURSOR_WAIT.subscribe(
            lambda wait: wx.SetCursor(wx.Cursor(wx.CURSOR_WAIT)) if wait else wx.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        )

    def __enter__(self):
        self.CURSOR_WAIT.set_value(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.CURSOR_WAIT.set_value(False)

    def __call__(self, *args, **kwargs):
        return self.__enter__()
