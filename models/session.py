import copy
import enum
import dataclasses
from typing import NamedTuple, Union, Type, Optional, Any, Callable, List

import wx

from models.structures.datatype import StandardDataType
from models.structures.statement import AbstractStatement

from models.structures.mariadb.datatype import MariaDBDataType
from models.structures.mariadb.statement import MariaDBStatement
from models.structures.mysql.datatype import MySQLDataType
from models.structures.mysql.statment import MySQLStatement
from models.structures.postgresql.datatype import PostgreSQLDataType
from models.structures.postgresql.statement import PostgreSQLStatement
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.sqlite.statment import SQLiteStatement


class SessionEngine(enum.Enum):
    MYSQL = "MySQL"
    MARIADB = "MariaDB"
    POSTGRESQL = "PostgreSQL"
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

    _id: Optional[str] = None
    _datatype: Optional[StandardDataType] = None
    _statement: Optional[AbstractStatement] = None
    # _control: Optional[wx.Control] = None

    @property
    def statement(self) -> AbstractStatement:
        if self._statement is None:
            if self.engine == SessionEngine.MYSQL:
                self._statement = MySQLStatement(self)
            elif self.engine == SessionEngine.MARIADB:
                self._statement = MariaDBStatement(self)
            elif self.engine == SessionEngine.POSTGRESQL:
                self._statement = PostgreSQLStatement(self)
            elif self.engine == SessionEngine.SQLITE:
                self._statement = SQLiteStatement(self)
            else:
                raise ValueError(f"Unsupported engine {self.engine}")

        return self._statement

    @property
    def datatype(self) -> StandardDataType:
        if self._datatype is None:
            if self.engine == SessionEngine.MYSQL:
                self._datatype = MySQLDataType()
            elif self.engine == SessionEngine.MARIADB:
                self._datatype = MariaDBDataType()
            elif self.engine == SessionEngine.POSTGRESQL:
                self._datatype = PostgreSQLDataType()
            elif self.engine == SessionEngine.SQLITE:
                self._datatype = SQLiteDataType()
            else:
                raise ValueError(f"Unsupported engine {self.engine}")

        return self._datatype

    def to_dict(self):
        return {
            'name': self.name,
            'engine': self.engine.value if self.engine else None,
            'configuration': self.configuration._asdict() if self.configuration else None,
            'comments': self.comments
        }

    def is_valid(self):
        return all([self.name, self.engine]) and all(self.configuration._asdict().values())
