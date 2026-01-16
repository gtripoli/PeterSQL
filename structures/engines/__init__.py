import enum

from functools import lru_cache
from typing import List, NamedTuple

import wx

from icons import BitmapList


class Engine(NamedTuple):
    name: str
    dialect: str
    bitmap: wx.Bitmap

class SessionEngine(enum.Enum):
    SQLITE = Engine("SQLite", "sqlite", BitmapList.ENGINE_SQLITE)
    MARIADB = Engine("MariaDB", "mariadb", BitmapList.ENGINE_MARIADB)
    MYSQL = Engine("MySQL", "mariasql", BitmapList.ENGINE_MYSQL)
    POSTGRESQL = Engine("PostgreSQL", "postgresql", BitmapList.ENGINE_POSTGRESQL)

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
