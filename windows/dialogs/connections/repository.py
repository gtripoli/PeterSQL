from pathlib import Path
from typing import Any, Optional, Union

from constants import WORKDIR
from helpers.logger import logger
from helpers.observables import ObservableLazyList
from helpers.repository import YamlRepository

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
        payload = [item.to_dict() for item in connections]
        self._write_yaml(payload)

    def load(self) -> list[Union[ConnectionDirectory, Connection]]:
        data = self._read()
        logger.debug(
            f"ConnectionsRepository.load: loading {len(data)} items from {self._config_file}"
        )
        result = [self._item_from_dict(item) for item in data]
        logger.debug(
            f"ConnectionsRepository.load: loaded {len(result)} connections/directories"
        )
        return result

    def _item_from_dict(
        self, data: dict[str, Any], parent: Optional[ConnectionDirectory] = None
    ) -> Union[ConnectionDirectory, Connection]:
        if data.get("type") == "directory":
            directory = ConnectionDirectory(name=data["name"], children=[])
            children = [
                self._item_from_dict(child_data, directory)
                for child_data in data.get("children", [])
            ]
            directory.children = children
            return directory
        else:
            return self._connection_from_dict(data)

    def _connection_from_dict(self, data: dict[str, Any]) -> Connection:
        engine = ConnectionEngine.from_name(
            data.get("engine", ConnectionEngine.MYSQL.value.name)
        )

        configuration: Optional[
            Union[CredentialsConfiguration, SourceConfiguration]
        ] = None

        if data.get("configuration"):
            config_data = data["configuration"]
            if engine in [
                ConnectionEngine.MYSQL,
                ConnectionEngine.MARIADB,
                ConnectionEngine.POSTGRESQL,
            ]:
                configuration = CredentialsConfiguration(**config_data)
            elif engine == ConnectionEngine.SQLITE:
                configuration = SourceConfiguration(**config_data)

        ssh_config = self._build_ssh_configuration(data.get("ssh_tunnel", {}))

        if data.get("id") is not None:
            self._id_counter = max(self._id_counter, data["id"] + 1)

        comments = data.get("comments")
        if comments is None:
            comments = ""

        return Connection(
            id=data["id"],
            name=data["name"],
            engine=engine,
            configuration=configuration,
            comments=comments,
            ssh_tunnel=ssh_config,
        )

    def add_connection(
        self, connection: Connection, parent: Optional[ConnectionDirectory] = None
    ) -> int:
        self.connections.get_value()

        if connection.is_new:
            connection.id = self._next_id()

        if parent:
            parent.children.append(connection)
        else:
            self.connections.append(connection)

        self._write()
        self.connections.refresh()

        return connection.id

    def save_connection(self, connection: Connection) -> int:
        self.connections.get_value()

        def _find_and_replace(connections, target_id):
            for i, item in enumerate(connections):
                if isinstance(item, ConnectionDirectory):
                    if _find_and_replace(item.children, target_id):
                        return True
                elif isinstance(item, Connection) and item.id == target_id:
                    connections[i] = connection
                    return True
            return False

        if _find_and_replace(self.connections.get_value(), connection.id):
            self._write()
            self.connections.refresh()

        return connection.id

    def save_directory(self, directory: ConnectionDirectory) -> None:
        self.connections.append(directory, replace_existing=True)

        self._write()

    def add_directory(
        self,
        directory: ConnectionDirectory,
        parent: Optional[ConnectionDirectory] = None,
    ) -> None:
        self.connections.get_value()

        if parent:
            parent.children.append(directory)
        else:
            self.connections.append(directory)

        self._write()

    def delete_directory(self, directory: ConnectionDirectory):
        self.connections.get_value()

        def _find_and_delete(
            nodes: list[Union[ConnectionDirectory, Connection]],
            target: ConnectionDirectory,
        ):
            for idx, item in enumerate(nodes):
                if isinstance(item, ConnectionDirectory):
                    if item == target:
                        del nodes[idx]
                        return True

                    if _find_and_delete(item.children, target):
                        return True

            return False

        if _find_and_delete(self.connections.get_value(), directory):
            self._write()
            self.connections.refresh()

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
                extra_args=data.get("extra_args"),
            )
        except (TypeError, ValueError):
            return None
