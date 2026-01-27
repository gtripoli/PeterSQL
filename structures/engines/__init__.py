import enum

from functools import lru_cache
from typing import List, NamedTuple

import wx

from icons import IconList, Icon


class Engine(NamedTuple):
    name: str
    dialect: str
    bitmap: Icon


class ConnectionEngine(enum.Enum):
    SQLITE = Engine("SQLite", "sqlite", IconList.SQLITE)
    MARIADB = Engine("MariaDB", "mysql", IconList.MARIADB)
    MYSQL = Engine("MySQL", "mysql", IconList.MYSQL)
    POSTGRESQL = Engine("PostgreSQL", "postgres", IconList.POSTGRESQL)

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
