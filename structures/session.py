import contextlib
import dataclasses

from typing import Union, Optional, Any

from structures.engines import SessionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration
from structures.engines.context import AbstractContext


@dataclasses.dataclass(eq=False)
class Session:
    id: int
    name: str
    engine: Optional[SessionEngine]
    configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]]
    comments: Optional[str] = None
    ssh_tunnel: Optional[SSHTunnelConfiguration] = None

    context: Optional[AbstractContext] = dataclasses.field(default=None, init=False, repr=False, compare=False)
    _ssh_tunnel_process: Any = dataclasses.field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.engine == SessionEngine.SQLITE:
            from structures.engines.sqlite.context import SQLiteContext

            self.context = SQLiteContext(self)

        elif self.engine == SessionEngine.MARIADB:
            from structures.engines.mariadb.context import MariaDBContext

            self.context = MariaDBContext(self)

        elif self.engine == SessionEngine.MYSQL:
            from structures.engines.mysql.context import MySQLContext

            self.context = MySQLContext(self)

        elif self.engine == SessionEngine.POSTGRESQL:
            pass

        else:
            raise ValueError(f"Unsupported engine {self.engine}")

    def __eq__(self, other: Any):
        if not isinstance(other, Session):
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

    @property
    def tunnel_process(self):
        return getattr(self, "_ssh_tunnel_process", None)

    def set_tunnel_process(self, process: Any):
        self._ssh_tunnel_process = process

    def stop_tunnel(self):
        if process := getattr(self, "_ssh_tunnel_process", None):
            with contextlib.suppress(Exception):
                process.terminate()
                process.wait(timeout=1)
            self._ssh_tunnel_process = None
