import dataclasses
import enum

from functools import lru_cache
from typing import Union, Optional, Any, NamedTuple

from icons import Icon, IconList

from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration


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
    def get_all(cls) -> list["ConnectionEngine"]:
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
    name: str
    children: List[Union['ConnectionDirectory', 'Connection']] = dataclasses.field(default_factory=list)

    def to_dict(self):
        return {
            'type': 'directory',
            'name': self.name,
            'children': [child.to_dict() for child in self.children]
        }


@dataclasses.dataclass(eq=False)
class Connection:
    """Persistent configuration only. No runtime state."""
    id: int
    name: str
    engine: ConnectionEngine
    configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]]
    comments: Optional[str] = ""
    ssh_tunnel: Optional[SSHTunnelConfiguration] = None

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
            'id': self.id,
            'type': 'connection',
            'name': self.name,
            'engine': self.engine.value.name if self.engine else None,
            'configuration': self.configuration._asdict() if self.configuration else None,
            'comments': self.comments,
            'ssh_tunnel': self.ssh_tunnel._asdict() if self.ssh_tunnel else None
        }

    @property
    def is_valid(self):
        return all([self.name, self.engine]) and all(self.configuration._asdict().values())

    @property
    def is_new(self):
        return self.id <= -1

    def has_enabled_tunnel(self) -> bool:
        return bool(self.ssh_tunnel and self.ssh_tunnel.is_enabled)
