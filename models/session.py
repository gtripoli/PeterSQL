import copy
import enum
import dataclasses
from typing import NamedTuple, Union, Type, Optional, Any, Callable, List

import wx

from helpers.lazylist import LazyList
from models.database import Database
from models.structures.statement import AbstractStatement
from models.structures.mysql.statment import MySQLStatement
from models.structures.sqlite.statment import SQLiteStatement
from models.structures.mariadb.statment import MariaDBStatement


class SessionEngine(enum.Enum):
    MYSQL = "MySQL"
    MARIADB = "MariaDB"
    SQLITE = "SQLite"


class CredentialsConfiguration(NamedTuple):
    hostname: str
    username: str
    password: str
    port: int


class SourceConfiguration(NamedTuple):
    filename: str


@dataclasses.dataclass
class Session:
    name: str
    engine: SessionEngine | None
    configuration: Union[CredentialsConfiguration, SourceConfiguration] | None
    comments: Optional[str] = None

    _id: str = None
    _statement: AbstractStatement = None
    _control: Optional[wx.Control] = None


    @property
    def statement(self) -> AbstractStatement:
        if self._statement is None:
            if self.engine == SessionEngine.MYSQL:
                self._statement = MySQLStatement(self)
            elif self.engine == SessionEngine.MARIADB:
                self._statement = MariaDBStatement(self)
            elif self.engine == SessionEngine.SQLITE:
                self._statement = SQLiteStatement(self)
            else:
                raise ValueError(f"Unsupported engine {self.engine}")

        return self._statement

    def to_dict(self):
        attributes = copy.copy(self.__dict__)
        del attributes["control"]

        result = dict(attributes, **dict(engine=self.engine.value, configuration=self.configuration._asdict()))

        return result

    def is_valid(self):
        return all([self.name, self.engine]) and all(self.configuration._asdict().values())

    # def __eq__(self, other: 'Session'):
    #     if isinstance(other, Session):
    #         return self.to_dict() == other.to_dict()
    #
    #     return False
