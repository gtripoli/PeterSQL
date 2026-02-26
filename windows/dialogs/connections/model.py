from gettext import gettext as _

from helpers import wx_call_after_debounce
from helpers.bindings import AbstractModel
from helpers.observables import Observable, CallbackEvent

from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration

from . import CURRENT_CONNECTION, PENDING_CONNECTION


class ConnectionModel(AbstractModel):
    def __init__(self):
        self.name = Observable[str]()
        self.engine = Observable[str](initial=ConnectionEngine.MYSQL.value.name)
        self.hostname = Observable[str]()
        self.username = Observable[str]()
        self.password = Observable[str]()
        self.port = Observable[int](initial=3306)
        self.filename = Observable[str]()
        self.comments = Observable[str]("")

        self.ssh_tunnel_enabled = Observable[bool](initial=False)
        self.ssh_tunnel_executable = Observable[str](initial="ssh")
        self.ssh_tunnel_hostname = Observable[str]()
        self.ssh_tunnel_port = Observable[int](initial=22)
        self.ssh_tunnel_username = Observable[str]()
        self.ssh_tunnel_password = Observable[str]()
        self.ssh_tunnel_local_port = Observable[int](initial=3307)

        self.engine.subscribe(self._set_default_port)

        wx_call_after_debounce(
            self.name, self.engine, self.hostname, self.username, self.password, self.port,
            self.filename, self.comments,
            self.ssh_tunnel_enabled, self.ssh_tunnel_executable, self.ssh_tunnel_hostname,
            self.ssh_tunnel_port, self.ssh_tunnel_username, self.ssh_tunnel_password, self.ssh_tunnel_local_port,
            callback=self._build
        )

        CURRENT_CONNECTION.subscribe(self.clear, CallbackEvent.BEFORE_CHANGE)
        CURRENT_CONNECTION.subscribe(self.apply, CallbackEvent.AFTER_CHANGE)

    def _set_default_port(self, connection_engine_name: str):
        connection_engine = ConnectionEngine.from_name(connection_engine_name)
        if connection_engine == ConnectionEngine.POSTGRESQL:
            self.port(5432)
        elif connection_engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB]:
            self.port(3306)

    def clear(self, *args):
        defaults = {
            self.name: None,
            self.engine: ConnectionEngine.MYSQL.value.name,
            self.hostname: None, self.username: None, self.password: None, self.port: 3306,
            self.filename: None,
            self.comments: None,
            self.ssh_tunnel_enabled: False, self.ssh_tunnel_executable: "ssh", self.ssh_tunnel_hostname: None,
            self.ssh_tunnel_port: 22, self.ssh_tunnel_username: None, self.ssh_tunnel_password: None,
            self.ssh_tunnel_local_port: 3307,
        }

        for observable, value in defaults.items():
            observable(value)

    def apply(self, connection: Connection):
        if not connection:
            return

        self.name(connection.name)

        if connection.engine is not None:
            self.engine(connection.engine.value.name)

        self.comments(connection.comments)

        if isinstance(connection.configuration, CredentialsConfiguration):
            self.hostname(connection.configuration.hostname)
            self.username(connection.configuration.username)
            self.password(connection.configuration.password)
            self.port(connection.configuration.port)

        elif isinstance(connection.configuration, SourceConfiguration):
            self.filename(connection.configuration.filename)

        if ssh_tunnel := connection.ssh_tunnel:
            self.ssh_tunnel_enabled(ssh_tunnel.enabled)
            self.ssh_tunnel_executable(ssh_tunnel.executable)
            self.ssh_tunnel_hostname(ssh_tunnel.hostname)
            self.ssh_tunnel_port(ssh_tunnel.port)
            self.ssh_tunnel_username(ssh_tunnel.username)
            self.ssh_tunnel_password(ssh_tunnel.password)
            self.ssh_tunnel_local_port(ssh_tunnel.local_port)
        else:
            self.ssh_tunnel_enabled(False)

    def _build_empty_connection(self):
        return Connection(
            id=-1,
            name=self.name() or _("New connection"),
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="",
                port=3306
            )
        )

    def _build(self, *args):
        if any([self.name.is_empty, self.engine.is_empty]):
            return

        current_connection = CURRENT_CONNECTION()
        pending_connection = PENDING_CONNECTION()

        if not pending_connection:
            pending_connection = current_connection.copy() if current_connection else self._build_empty_connection()

        connection_engine = ConnectionEngine.from_name(self.engine())

        pending_connection.name = self.name() or ""
        pending_connection.engine = connection_engine
        pending_connection.comments = self.comments()

        if connection_engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.POSTGRESQL]:
            pending_connection.configuration = CredentialsConfiguration(
                hostname=self.hostname.get_value() or "localhost",
                username=self.username.get_value() or "root",
                password=self.password.get_value() or "",
                port=self.port.get_value() or 3306
            )

            if ssh_tunnel_enabled := bool(self.ssh_tunnel_enabled()):
                pending_connection.ssh_tunnel = SSHTunnelConfiguration(
                    enabled=ssh_tunnel_enabled,
                    executable=self.ssh_tunnel_executable.get_value() or "ssh",
                    hostname=self.ssh_tunnel_hostname.get_value() or "",
                    port=self.ssh_tunnel_port.get_value() or 22,
                    username=self.ssh_tunnel_username.get_value(),
                    password=self.ssh_tunnel_password.get_value(),
                    local_port=self.ssh_tunnel_local_port.get_value(),
                )

        elif connection_engine == ConnectionEngine.SQLITE:
            pending_connection.configuration = SourceConfiguration(
                filename=self.filename()
            )
            pending_connection.ssh_tunnel = None

        if not pending_connection.is_valid:
            return

        if pending_connection == current_connection:
            return

        PENDING_CONNECTION(pending_connection)
