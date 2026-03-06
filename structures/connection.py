import dataclasses
import enum

from functools import lru_cache
from typing import Any, NamedTuple, Optional, Union

from icons import Icon, IconList

from structures.configurations import (
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)


class Engine(NamedTuple):
    name: str
    dialect: str
    bitmap: Icon


class ConnectionEngine(enum.Enum):
    SQLITE = Engine("SQLite", "sqlite", IconList.SQLITE)
    MARIADB = Engine("MariaDB", "mysql", IconList.MARIADB)
    MYSQL = Engine("MySQL", "mysql", IconList.MYSQL)
    POSTGRESQL = Engine("PostgreSQL", "postgres", IconList.POSTGRESQL)
    ORACLE = Engine("Oracle", "oracle", IconList.ORACLE)

    @classmethod
    def get_all(cls) -> list[Engine]:
        return [e.value for e in list(cls)]

    @classmethod
    @lru_cache(maxsize=None)
    def from_name(cls, name: str) -> "ConnectionEngine":
        for engine in cls:
            if engine.value.name == name:
                return engine
        raise ValueError(f"ConnectionEngine not found for name: {name}")


@dataclasses.dataclass
class ConnectionDirectory:
    id: int
    name: str
    children: list[Union["ConnectionDirectory", "Connection"]] = dataclasses.field(
        default_factory=list
    )

    def to_dict(self):
        return {
            "id": self.id,
            "type": "directory",
            "name": self.name,
            "children": [child.to_dict() for child in self.children],
        }

    @property
    def is_new(self) -> bool:
        return self.id <= -1


@dataclasses.dataclass(eq=False)
class Connection:
    """Persistent configuration only. No runtime state."""

    id: int
    name: str
    engine: ConnectionEngine
    configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]]
    comments: Optional[str] = ""
    ssh_tunnel: Optional[SSHTunnelConfiguration] = None
    parent: Optional["ConnectionDirectory"] = dataclasses.field(
        default=None,
        compare=False,
        repr=False,
    )
    created_at: Optional[str] = None
    last_connection_at: Optional[str] = None
    last_successful_connection_at: Optional[str] = None
    last_failure_reason: Optional[str] = None
    successful_connections: int = 0
    unsuccessful_connections: int = 0
    total_connection_attempts: int = 0
    average_connection_time_ms: Optional[int] = None
    most_recent_connection_duration_ms: Optional[int] = None

    def __eq__(self, other: Any):
        if not isinstance(other, Connection):
            return False

        for field in dataclasses.fields(self):
            if not field.compare:
                continue

            if getattr(self, field.name) != getattr(other, field.name):
                return False

        return True

    def copy(self):
        return dataclasses.replace(self)

    def to_dict(self):
        return {
            "id": self.id,
            "type": "connection",
            "name": self.name,
            "engine": self.engine.value.name if self.engine else None,
            "configuration": self.configuration._asdict()
            if self.configuration
            else None,
            "comments": self.comments,
            "ssh_tunnel": self.ssh_tunnel._asdict() if self.ssh_tunnel else None,
            "created_at": self.created_at,
            "last_connection_at": self.last_connection_at,
            "last_successful_connection_at": self.last_successful_connection_at,
            "last_failure_reason": self.last_failure_reason,
            "successful_connections": self.successful_connections,
            "unsuccessful_connections": self.unsuccessful_connections,
            "total_connection_attempts": self.total_connection_attempts,
            "average_connection_time_ms": self.average_connection_time_ms,
            "most_recent_connection_duration_ms": self.most_recent_connection_duration_ms,
        }

    @property
    def is_valid(self):
        if not self.name or not self.engine or not self.configuration:
            return False

        configuration = self.configuration._asdict()
        for key, value in configuration.items():
            if isinstance(value, bool):
                continue

            if key == "password":
                continue

            if value is None:
                return False

            if isinstance(value, str) and value == "":
                return False

        return True

    @property
    def is_new(self):
        return self.id <= -1

    def has_enabled_tunnel(self) -> bool:
        return bool(self.ssh_tunnel and self.ssh_tunnel.is_enabled)
