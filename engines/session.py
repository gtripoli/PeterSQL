import enum
import dataclasses
from typing import NamedTuple, Union, Optional

from engines.structures.context import AbstractContext
from engines.structures.indextype import StandardIndexType
from engines.structures.datatype import StandardDataType

from engines.structures.mariadb.context import MariaDBContext
from engines.structures.mariadb.datatype import MariaDBDataType
from engines.structures.mariadb.indextype import MariaDBIndexType
#
# from engines.structures.mysql.statement import MySQLStatement
# from engines.structures.mysql.datatype import MySQLDataType
# from engines.structures.mysql.indextype import MySQLIndexType

from engines.structures.sqlite.context import SQLiteContext
from engines.structures.sqlite.datatype import SQLiteDataType
from engines.structures.sqlite.indextype import SQLiteIndexType


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
    id: Union[int, str]
    name: str
    engine: SessionEngine | None
    configuration: Union[CredentialsConfiguration, SourceConfiguration] | None
    comments: Optional[str] = None


    context: Optional[AbstractContext] = dataclasses.field(init=False)
    datatype: Optional[StandardDataType] = dataclasses.field(init=False)
    indextype: Optional[StandardIndexType] = dataclasses.field(init=False)

    def __post_init__(self):
        if self.engine == SessionEngine.MYSQL:
            # self.statement = MySQLStatement(self)
            # self.datatype = MySQLDataType()
            # self.indextype = MySQLIndexType()
            pass
        elif self.engine == SessionEngine.MARIADB:
            self.context = MariaDBContext(self)
            self.datatype = MariaDBDataType()
            self.indextype = MariaDBIndexType()
        elif self.engine == SessionEngine.POSTGRESQL:
            pass
        #     self.statement = PostgreSQLStatement(self)
        #     self.datatype = PostgreSQLDataType()
            # self.indextype = PostgreSQLIndexType()
        elif self.engine == SessionEngine.SQLITE:
            self.context = SQLiteContext(self)
            self.datatype = SQLiteDataType()
            self.indextype = SQLiteIndexType()

        else :
            raise ValueError(f"Unsupported engine {self.engine}")

    def to_dict(self):
        return {
            'name': self.name,
            'engine': self.engine.value if self.engine else None,
            'configuration': self.configuration._asdict() if self.configuration else None,
            'comments': self.comments
        }

    def is_valid(self):
        return all([self.name, self.engine]) and all(self.configuration._asdict().values())
