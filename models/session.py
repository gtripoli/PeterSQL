import enum
import dataclasses
from typing import NamedTuple, Union, Optional

from models.structures.indextype import StandardIndexType
from models.structures.datatype import StandardDataType
from models.structures.statement import AbstractStatement

# from models.structures.mariadb.statement import MariaDBStatement
# from models.structures.mariadb.datatype import MariaDBDataType
# from models.structures.mariadb.indextype import MariaDBIndexType
#
# from models.structures.mysql.statement import MySQLStatement
# from models.structures.mysql.datatype import MySQLDataType
# from models.structures.mysql.indextype import MySQLIndexType

from models.structures.sqlite.statment import SQLiteStatement
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.sqlite.indextype import SQLiteIndexType


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
    statement: Optional[AbstractStatement] = dataclasses.field(init=False)

    datatype: Optional[StandardDataType] = dataclasses.field(init=False)
    indextype: Optional[StandardIndexType] = dataclasses.field(init=False)

    def __post_init__(self):
        if self.engine == SessionEngine.MYSQL:
            # self.statement = MySQLStatement(self)
            # self.datatype = MySQLDataType()
            # self.indextype = MySQLIndexType()
            pass
        elif self.engine == SessionEngine.MARIADB:
            # self.statement = MariaDBStatement(self)
            # self.datatype = MariaDBDataType()
            # self.indextype = MariaDBIndexType()
            pass
        elif self.engine == SessionEngine.POSTGRESQL:
            pass
        #     self.statement = PostgreSQLStatement(self)
        #     self.datatype = PostgreSQLDataType()
            # self.indextype = PostgreSQLIndexType()
        elif self.engine == SessionEngine.SQLITE:
            self.statement = SQLiteStatement(self)
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
