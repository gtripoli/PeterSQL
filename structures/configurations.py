import enum
from typing import NamedTuple


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


class SSHTunnelConfiguration(NamedTuple):
    enabled: bool
    executable: str
    hostname: str
    port: int
    username: str
    password: str
    local_port: int

    @property
    def is_enabled(self) -> bool:
        return bool(
            self.enabled
            and self.executable
            and self.hostname
            and self.username
            and self.local_port
        )
