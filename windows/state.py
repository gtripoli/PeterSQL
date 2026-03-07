from helpers.observables import Observable, ObservableList

from structures.session import Session
from structures.connection import Connection
from structures.engines.database import SQLColumn, SQLDatabase, SQLForeignKey, SQLIndex, SQLRecord, SQLTable, SQLTrigger, SQLView

SESSIONS_LIST: ObservableList[Session] = ObservableList()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_CONNECTION: Observable[Connection] = Observable()
CURRENT_DATABASE: Observable[SQLDatabase] = Observable()
CURRENT_TABLE: Observable[SQLTable] = Observable()
CURRENT_VIEW: Observable[SQLView] = Observable()
CURRENT_TRIGGER: Observable[SQLTrigger] = Observable()
CURRENT_FUNCTION: Observable[SQLTrigger] = Observable()
CURRENT_PROCEDURE: Observable[SQLTrigger] = Observable()
CURRENT_EVENT: Observable[SQLTrigger] = Observable()
CURRENT_COLUMN: Observable[SQLColumn] = Observable()
CURRENT_INDEX: Observable[SQLIndex] = Observable()
CURRENT_FOREIGN_KEY: Observable[SQLForeignKey] = Observable()
CURRENT_RECORDS: ObservableList[SQLRecord] = ObservableList()

NEW_TABLE: Observable[SQLTable] = Observable()

AUTO_APPLY: Observable[bool] = Observable(True)
