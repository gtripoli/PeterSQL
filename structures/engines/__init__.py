import enum

from functools import lru_cache
from typing import List, NamedTuple

import wx

from icons import BitmapList


class Engine(NamedTuple):
    name: str
    dialect: str
    bitmap: wx.Bitmap

class ConnectionEngine(enum.Enum):
    SQLITE = Engine("SQLite", "sqlite", BitmapList.ENGINE_SQLITE)
    MARIADB = Engine("MariaDB", "mysql", BitmapList.ENGINE_MARIADB)
    MYSQL = Engine("MySQL", "mysql", BitmapList.ENGINE_MYSQL)
    POSTGRESQL = Engine("PostgreSQL", "postgresql", BitmapList.ENGINE_POSTGRESQL)

    @classmethod
    def get_all(cls) -> List["ConnectionEngine"]:
        return [e.value for e in list(cls)]

    @classmethod
    @lru_cache(maxsize=None)
    def from_name(cls, name: str) -> "ConnectionEngine":
        for engine in cls:
            if engine.value.name == name:
                return engine
        raise ValueError(f"ConnectionEngine not found for name: {name}")
