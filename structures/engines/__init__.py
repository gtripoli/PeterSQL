import enum

from functools import lru_cache
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

    @classmethod
    def get_all(cls) -> List["SessionEngine"]:
        return [e.value for e in list(cls)]

    @classmethod
    @lru_cache(maxsize=None)
    def from_name(cls, name: str) -> "SessionEngine":
        for engine in cls:
            if engine.value.name == name:
                return engine
        raise ValueError(f"SessionEngine not found for name: {name}")


def merge_original_current(original: MergeTypes, current_columns: MergeTypes):
    orig = {o.id: o for o in original}
    return [(orig.pop(c.id, None), c) for c in current_columns] + [(o, None) for o in orig.values()]
