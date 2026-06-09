import uuid
from pathlib import Path
from typing import Any, Optional, Union

from constants import WORKDIR
from helpers.logger import logger
from helpers.observables import ObservableLazyList
from helpers.repository import YamlRepository

from structures.secrets import (
    _is_legacy_numeric_id,
    delete_database_password,
    delete_ssh_password,
    get_database_password,
    get_ssh_password,
    set_database_password,
    set_ssh_password,
)

from windows.dialogs.connections import ConnectionDirectory

from structures.connection import (
    Connection,
    ConnectionEngine,
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)

CONNECTIONS_CONFIG_FILE = WORKDIR / "connections.yml"


class ConnectionsRepository(
    YamlRepository[list[Union[ConnectionDirectory, Connection]]]
):
    def __init__(self, config_file: Optional[str] = None):
        super().__init__(Path(config_file or CONNECTIONS_CONFIG_FILE))
        self._id_counter = 0
        self.connections = ObservableLazyList(self.load)

    def _next_id(self):
        id = self._id_counter
        self._id_counter += 1
        return id

    def _read(self) -> list[dict[str, Any]]:
        data = self._read_yaml()
        if isinstance(data, list):
            return data
        return []

    def _write(self) -> None:
        connections = self.connections.get_value()
        payload = [self._prepare_connection_dict(item) for item in connections]
        self._write_yaml(payload)

    def load(self) -> list[Union[ConnectionDirectory, Connection]]:
        data = self._read()
        self._id_counter = 0
        return [self._item_from_dict(item) for item in data]

    def _item_from_dict(
        self, data: dict[str, Any], parent: Optional[ConnectionDirectory] = None
    ) -> Union[ConnectionDirectory, Connection]:
        if data.get("type") == "directory":
            directory_id = data.get("id")
            if directory_id is not None:
                self._id_counter = max(self._id_counter, int(directory_id) + 1)
            else:
                logger.warning(
                    "Directory '%s' has no id. Fallback id=-1 will be used.",
                    data.get("name", "<unknown>"),
                )
                directory_id = -1

            directory = ConnectionDirectory(
                id=int(directory_id),
                name=data["name"],
                children=[],
            )
            children = [
                self._item_from_dict(child_data, directory)
                for child_data in data.get("children", [])
            ]
            directory.children = children
            return directory
        else:
            return self._connection_from_dict(data, parent)

    def _connection_from_dict(
        self,
        data: dict[str, Any],
        parent: Optional[ConnectionDirectory] = None,
    ) -> Connection:
        engine = ConnectionEngine.from_name(
            data.get("engine", ConnectionEngine.MYSQL.value.name)
        )

        configuration: Optional[
            Union[CredentialsConfiguration, SourceConfiguration]
        ] = None

        secret_id = data.get("secret_id")
        if secret_id is None:
            secret_id = str(uuid.uuid4())

        if data.get("configuration"):
            config_data = dict(data["configuration"])
            if engine in [
                ConnectionEngine.MYSQL,
                ConnectionEngine.MARIADB,
                ConnectionEngine.POSTGRESQL,
            ]:
                password_keyring_id = config_data.pop("password_keyring_id", None)
                if password_keyring_id is not None:
                    if _is_legacy_numeric_id(password_keyring_id):
                        legacy_password = get_database_password(password_keyring_id)
                        if legacy_password is not None:
                            set_database_password(secret_id, legacy_password)
                            delete_database_password(password_keyring_id)
                    else:
                        set_database_password(secret_id, get_database_password(password_keyring_id))
                    config_data["password"] = get_database_password(secret_id)
                configuration = self._build_credentials_configuration(config_data)
            elif engine == ConnectionEngine.SQLITE:
                configuration = SourceConfiguration(**config_data)

        ssh_tunnel_data = data.get("ssh_tunnel", {})
        ssh_password_keyring_id = ssh_tunnel_data.get("password_keyring_id")
        if ssh_password_keyring_id is not None:
            if _is_legacy_numeric_id(ssh_password_keyring_id):
                legacy_ssh_password = get_ssh_password(ssh_password_keyring_id)
                if legacy_ssh_password is not None:
                    set_ssh_password(secret_id, legacy_ssh_password)
                    delete_ssh_password(ssh_password_keyring_id)
            else:
                set_ssh_password(secret_id, get_ssh_password(ssh_password_keyring_id))
            ssh_tunnel_data = dict(ssh_tunnel_data)
            ssh_tunnel_data.pop("password_keyring_id", None)

        ssh_config = self._build_ssh_configuration(ssh_tunnel_data)

        if data.get("id") is not None:
            self._id_counter = max(self._id_counter, data["id"] + 1)

        comments = data.get("comments")
        if comments is None:
            comments = ""

        successful_connections = int(data.get("successful_connections", 0) or 0)
        unsuccessful_connections = int(data.get("unsuccessful_connections", 0) or 0)
        total_connection_attempts = int(data.get("total_connection_attempts", 0) or 0)

        average_connection_time_ms = data.get("average_connection_time_ms")
        if average_connection_time_ms is not None:
            average_connection_time_ms = int(average_connection_time_ms)

        most_recent_connection_duration_ms = data.get(
            "most_recent_connection_duration_ms"
        )
        if most_recent_connection_duration_ms is not None:
            most_recent_connection_duration_ms = int(most_recent_connection_duration_ms)

        return Connection(
            id=data["id"],
            name=data["name"],
            engine=engine,
            configuration=configuration,
            comments=comments,
            ssh_tunnel=ssh_config,
            read_only=bool(data.get("read_only", False)),
            parent=parent,
            created_at=data.get("created_at"),
            last_connection_at=data.get("last_connection_at"),
            last_successful_connection_at=data.get("last_successful_connection_at"),
            last_failure_reason=data.get("last_failure_reason"),
            successful_connections=successful_connections,
            unsuccessful_connections=unsuccessful_connections,
            total_connection_attempts=total_connection_attempts,
            average_connection_time_ms=average_connection_time_ms,
            most_recent_connection_duration_ms=most_recent_connection_duration_ms,
            secret_id=secret_id,
        )

    def add_connection(
        self, connection: Connection, parent: Optional[ConnectionDirectory] = None
    ) -> int:
        self.connections.get_value()

        if connection.is_new:
            connection.id = self._next_id()

        if connection.secret_id is None:
            connection.secret_id = str(uuid.uuid4())

        self._persist_connection_secrets(connection)

        if parent:
            parent.children.append(connection)
            connection.parent = parent
        else:
            self.connections.append(connection)
            connection.parent = None

        self._write()
        self.connections.refresh()

        return connection.id

    def save_connection(self, connection: Connection) -> int:
        self.connections.get_value()

        def _find_and_replace(
            connections: list[Union[ConnectionDirectory, Connection]],
            target_id: int,
            parent: Optional[ConnectionDirectory] = None,
        ) -> bool:
            for i, item in enumerate(connections):
                if isinstance(item, ConnectionDirectory):
                    if _find_and_replace(item.children, target_id, item):
                        return True
                elif isinstance(item, Connection) and item.id == target_id:
                    connection.parent = parent
                    connections[i] = connection
                    return True
            return False

        if connection.secret_id is None:
            connection.secret_id = str(uuid.uuid4())

        self._persist_connection_secrets(connection)

        if _find_and_replace(self.connections.get_value(), connection.id):
            self._write()
            self.connections.refresh()

        return connection.id

    def save_directory(self, directory: ConnectionDirectory) -> None:
        self.connections.get_value()

        def _find_and_replace(
            nodes: list[Union[ConnectionDirectory, Connection]],
            target_id: int,
            parent: Optional[ConnectionDirectory] = None,
        ) -> bool:
            for index, node in enumerate(nodes):
                if isinstance(node, ConnectionDirectory):
                    if node.id == target_id:
                        directory.children = node.children
                        nodes[index] = directory
                        return True

                    if _find_and_replace(node.children, target_id, node):
                        return True

            return False

        if _find_and_replace(self.connections.get_value(), directory.id):
            self._write()
            self.connections.refresh()

    def add_directory(
        self,
        directory: ConnectionDirectory,
        parent: Optional[ConnectionDirectory] = None,
    ) -> None:
        self.connections.get_value()

        if directory.is_new:
            directory.id = self._next_id()

        if parent:
            parent.children.append(directory)
        else:
            self.connections.append(directory)

        self._write()
        self.connections.refresh()

    def delete_directory(self, directory: ConnectionDirectory):
        self.connections.get_value()
        target_id = directory.id

        def _find_and_delete(
            nodes: list[Union[ConnectionDirectory, Connection]],
            target: ConnectionDirectory,
        ):
            for idx, item in enumerate(nodes):
                if isinstance(item, ConnectionDirectory):
                    if item.id == target_id:
                        del nodes[idx]
                        return True

                    if _find_and_delete(item.children, target):
                        return True

            return False

        if _find_and_delete(self.connections.get_value(), directory):
            self._write()
            self.connections.refresh()

    def find_connection_parent_directory(
        self, connection_id: int
    ) -> Optional[ConnectionDirectory]:
        self.connections.get_value()

        def _walk(
            nodes: list[Union[ConnectionDirectory, Connection]],
            parent: Optional[ConnectionDirectory] = None,
        ) -> Optional[ConnectionDirectory]:
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    if result := _walk(node.children, node):
                        return result
                    continue

                if isinstance(node, Connection) and node.id == connection_id:
                    node.parent = parent
                    return parent

            return None

        return _walk(self.connections.get_value())

    def get_all_connection_names(self) -> set[str]:
        self.connections.get_value()
        names: set[str] = set()

        def _walk(nodes: list[Union[ConnectionDirectory, Connection]]) -> None:
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    _walk(node.children)
                    continue

                if isinstance(node, Connection):
                    names.add(node.name)

        _walk(self.connections.get_value())
        return names

    def delete_connection(self, connection: Connection) -> None:
        self.connections.get_value()

        def _find_and_delete(connections, target_id):
            for i, item in enumerate(connections):
                if isinstance(item, ConnectionDirectory):
                    if _find_and_delete(item.children, target_id):
                        return True
                elif isinstance(item, Connection) and item.id == target_id:
                    del connections[i]
                    return True
            return False

        if _find_and_delete(self.connections.get_value(), connection.id):
            self._delete_connection_secrets(connection)
            self._write()
            self.connections.refresh()

    def _build_ssh_configuration(
        self, data: dict[str, Any]
    ) -> Optional[SSHTunnelConfiguration]:
        if not data:
            return None

        try:
            return SSHTunnelConfiguration(
                enabled=bool(data.get("enabled")),
                executable=data.get("executable", "ssh"),
                hostname=data.get("hostname", ""),
                port=int(data.get("port", 22)),
                username=data.get("username", ""),
                password=data.get("password", ""),
                local_port=int(data.get("local_port", 0)),
                remote_host=data.get("remote_host"),
                remote_port=int(data["remote_port"])
                if data.get("remote_port")
                else None,
                identity_file=data.get("identity_file"),
                extra_args=self._normalize_ssh_extra_args(data.get("extra_args")),
            )
        except (TypeError, ValueError):
            return None

    def _build_credentials_configuration(
        self, data: dict[str, Any]
    ) -> Optional[CredentialsConfiguration]:
        if not data:
            return None

        try:
            return CredentialsConfiguration(
                hostname=str(data.get("hostname", "")),
                username=str(data.get("username", "")),
                password=data.get("password"),
                port=int(data.get("port", 3306)),
                use_tls=bool(
                    data.get("use_tls", data.get("use_tls_enabled", False))
                ),
                connect_timeout=int(data.get("connect_timeout", 10)),
                compressed_protocol=bool(data.get("compressed_protocol", False)),
            )
        except (TypeError, ValueError):
            return None

    def _prepare_connection_dict(
        self, item: Union["ConnectionDirectory", "Connection"]
    ) -> dict[str, Any]:
        data = item.to_dict()

        if isinstance(item, ConnectionDirectory):
            data["children"] = [
                self._prepare_connection_dict(child) for child in item.children
            ]
            return data

        secret_id = getattr(item, "secret_id", None) or str(item.id)

        configuration = data.get("configuration")
        if configuration:
            configuration = dict(configuration)
            password = configuration.pop("password", None)
            if password not in (None, ""):
                configuration.pop("password_keyring_id", None)
                set_database_password(secret_id, password)
            elif "password_keyring_id" in configuration:
                del configuration["password_keyring_id"]
            data["configuration"] = configuration

        ssh_tunnel = data.get("ssh_tunnel")
        if ssh_tunnel:
            ssh_tunnel = dict(ssh_tunnel)
            ssh_password = ssh_tunnel.pop("password", None)
            if ssh_password not in (None, ""):
                ssh_tunnel.pop("password_keyring_id", None)
                set_ssh_password(secret_id, ssh_password)
            elif "password_keyring_id" in ssh_tunnel:
                del ssh_tunnel["password_keyring_id"]
            data["ssh_tunnel"] = ssh_tunnel

        if secret_id is not None:
            data["secret_id"] = secret_id

        return data

    def _persist_connection_secrets(self, connection: Connection) -> None:
        secret_id = getattr(connection, "secret_id", None) or str(connection.id)
        if isinstance(connection.configuration, CredentialsConfiguration):
            set_database_password(secret_id, connection.configuration.password)

        if connection.ssh_tunnel:
            set_ssh_password(secret_id, connection.ssh_tunnel.password)

    def _delete_connection_secrets(self, connection: Connection) -> None:
        secret_id = getattr(connection, "secret_id", None) or str(connection.id)
        delete_database_password(secret_id)
        delete_ssh_password(secret_id)

    @staticmethod
    def _normalize_ssh_extra_args(extra_args: Any) -> Optional[Union[str, list[str]]]:
        if isinstance(extra_args, str):
            value = extra_args.strip()
            return value if value else None

        if isinstance(extra_args, list):
            values = [
                str(value).strip()
                for value in extra_args
                if isinstance(value, str) and value.strip()
            ]
            return values if values else None

        return None
