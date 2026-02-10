import contextlib
import dataclasses
import enum

from typing import Optional, Any, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from structures.engines.context import AbstractContext

from structures.connection import Connection, ConnectionEngine


class SessionState(enum.Enum):
    """Runtime state of a session."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LOADING = "loading"
    ERROR = "error"


@dataclasses.dataclass
class Session:
    """Runtime-only session. Owns context and all runtime state."""
    connection: Connection
    context: 'AbstractContext' = dataclasses.field(init=False, repr=False)
    state: SessionState = dataclasses.field(default=SessionState.DISCONNECTED, init=False)
    error: Optional[str] = dataclasses.field(default=None, init=False)
    _ssh_tunnel_process: Any = dataclasses.field(default=None, init=False, repr=False)

    def __post_init__(self):
        context_class = self._get_context_class()
        self.context = context_class(self.connection)

    @property
    def id(self) -> int:
        return self.connection.id

    @property
    def name(self) -> str:
        return self.connection.name

    @property
    def engine(self) -> ConnectionEngine:
        return self.connection.engine

    @property
    def configuration(self):
        return self.connection.configuration

    @property
    def is_connected(self) -> bool:
        return self.state == SessionState.CONNECTED and self.context.is_connected

    @property
    def ssh_tunnel_process(self) -> Any:
        return self._ssh_tunnel_process

    def _get_context_class(self) -> Type['AbstractContext']:
        """Return the context class for the given engine."""
        if self.engine == ConnectionEngine.SQLITE:
            from structures.engines.sqlite.context import SQLiteContext
            return SQLiteContext

        if self.engine == ConnectionEngine.MARIADB:
            from structures.engines.mariadb.context import MariaDBContext
            return MariaDBContext

        if self.engine == ConnectionEngine.MYSQL:
            from structures.engines.mysql.context import MySQLContext
            return MySQLContext

        if self.engine == ConnectionEngine.POSTGRESQL:
            from structures.engines.postgresql.context import PostgreSQLContext
            return PostgreSQLContext

        raise ValueError(f"Unsupported engine: {self.engine}")

    def set_state(self, state: SessionState) -> None:
        """Set the session state."""
        self.state = state

    def has_enabled_tunnel(self) -> bool:
        """Check if SSH tunnel is enabled."""
        return self.connection.has_enabled_tunnel()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Session):
            return False
        return self.connection == other.connection

    def __hash__(self) -> int:
        return hash(self.connection.id)

    def connect(self, **kwargs) -> None:
        """Connect to the database."""
        self.state = SessionState.CONNECTING
        self.error = None
        try:
            self.context.connect(**kwargs)
            self.state = SessionState.CONNECTED
        except Exception as ex:
            self.state = SessionState.ERROR
            self.error = str(ex)
            raise

    def disconnect(self) -> None:
        """Disconnect from the database and stop SSH tunnel."""
        self.context.disconnect()
        self.stop_tunnel()
        self.state = SessionState.DISCONNECTED

    def stop_tunnel(self) -> None:
        """Stop the SSH tunnel process if running."""
        if process := self._ssh_tunnel_process:
            with contextlib.suppress(Exception):
                process.terminate()
                process.wait(timeout=1)
            self._ssh_tunnel_process = None