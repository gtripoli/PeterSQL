import enum
from typing import List, Union, TypeAlias, NamedTuple

import wx

from icons import BitmapList
from structures.engines.database import SQLColumn, SQLIndex, SQLForeignKey

MergeTypes: TypeAlias = List[Union['SQLColumn', 'SQLIndex', 'SQLForeignKey']]


class Engine(NamedTuple):
    name: str
    bitmap: wx.Bitmap


class SessionEngine(enum.Enum):
    SQLITE = Engine("SQLite", BitmapList.ENGINE_SQLITE)
    MARIADB = Engine("MariaDB", BitmapList.ENGINE_MARIADB)
    MYSQL = Engine("MySQL", BitmapList.ENGINE_MYSQL)
    POSTGRESQL = Engine("PostgreSQL", BitmapList.ENGINE_POSTGRESQL)


def merge_original_current(original: MergeTypes, current_columns: MergeTypes):
    orig = {o.id: o for o in original}
    return [(orig.pop(c.id, None), c) for c in current_columns] + [(o, None) for o in orig.values()]
