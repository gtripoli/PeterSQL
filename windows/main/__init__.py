from helpers.observables import Observable, ObservableList

from structures.connection import Connection
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLForeignKey, SQLIndex, SQLRecord, SQLTrigger, SQLView

CONNECTIONS_LIST: ObservableList[Connection] = ObservableList()

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

AUTO_APPLY: Observable[bool] = Observable(True)

ENGINE_COMMON_KEYWORDS = (
    "select from where insert into values update set delete "
    "create alter drop rename "
    "table view index "
    "distinct as "
    "and or not "
    "null is in exists like between "
    "join inner left right full cross on using "
    "group by having "
    "order by "
    "limit offset fetch first rows only "
    "union union all intersect except "
    "case when then else end "
    "with recursive "
    "begin commit rollback savepoint release transaction "
    "primary key foreign key references unique check constraint "
    "default "
)
