from helpers.observables import Observable, ObservableArray
from models.session import Session
from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLForeignKey, SQLIndex, SQLRecord

SESSIONS: ObservableArray[Session] = ObservableArray()

CURRENT_SESSION: Observable[Session] = Observable()
CURRENT_DATABASE: Observable[SQLDatabase] = Observable()
CURRENT_TABLE: Observable[SQLTable] = Observable()
CURRENT_COLUMN: Observable[SQLColumn] = Observable()
CURRENT_INDEX: Observable[SQLIndex] = Observable()
CURRENT_FOREIGN_KEY: Observable[SQLForeignKey] = Observable()
CURRENT_RECORDS: ObservableArray[SQLRecord] = ObservableArray()

AUTO_APPLY: Observable[bool] = Observable(True)
