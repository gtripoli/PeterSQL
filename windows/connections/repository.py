import os
from typing import Any, Optional, Union

import yaml

from helpers.observables import ObservableList, ObservableLazyList

from windows.connections import ConnectionDirectory

from structures.connection import (
    Connection,
    ConnectionEngine,
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)

WORKDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONNECTIONS_CONFIG_FILE = os.path.join(WORKDIR, "connections.yml")


class ConnectionsRepository:
    def __init__(self, config_file: Optional[str] = None):
        self._config_file = config_file or CONNECTIONS_CONFIG_FILE
        self._id_counter = 0

        self.connections = ObservableLazyList(self.load)

    def _next_id(self):
        id = self._id_counter
        self._id_counter += 1
        return id

    def _read(self) -> list[dict[str, Any]]:
        try:
            connections = yaml.full_load(open(self._config_file))
            return connections or []
        except Exception:
            return []

    def _write(self) -> None:
        connections = self.connections.get_value()
        payload = [item.to_dict() for item in connections]
        with open(self._config_file, 'w') as file_handler:
            yaml.dump(payload, file_handler, sort_keys=False)

    def load(self) -> list[Union[ConnectionDirectory, Connection]]:
        return [self._item_from_dict(data) for data in self._read()]

    def _item_from_dict(self, data: dict[str, Any], parent: Optional[ConnectionDirectory] = None) -> Union[ConnectionDirectory, Connection]:
        if data.get('type') == 'directory':
            directory = ConnectionDirectory(name=data['name'], children=[])
            children = [self._item_from_dict(child_data, directory) for child_data in data.get('children', [])]
            directory.children = children
            return directory
        else:
            return self._connection_from_dict(data)

    def _connection_from_dict(self, data: dict[str, Any]) -> Connection:
        engine = ConnectionEngine.from_name(data.get('engine', ConnectionEngine.MYSQL.value.name))

        configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]] = None

        if data.get('configuration'):
            config_data = data['configuration']
            if engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.POSTGRESQL]:
                configuration = CredentialsConfiguration(**config_data)
            elif engine == ConnectionEngine.SQLITE:
                configuration = SourceConfiguration(**config_data)

        ssh_config = self._build_ssh_configuration(data.get('ssh_tunnel', {}))

        if data.get("id") is not None:
            self._id_counter = max(self._id_counter, data["id"] + 1)

        comments = data.get('comments')
        if comments is None:
            comments = ""

        return Connection(
            id=data["id"],
            name=data['name'],
            engine=engine,
            configuration=configuration,
            comments=comments,
            ssh_tunnel=ssh_config,
        )

    def add_connection(self, connection: Connection, parent: Optional[ConnectionDirectory] = None) -> int:

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

    def add_directory(self, directory: ConnectionDirectory, parent: Optional[ConnectionDirectory] = None) -> None:
        self.connections.get_value()

        if parent:
            parent.children.append(directory)
        else:
            self.connections.append(directory)

        self._write()

    def delete_directory(self, directory: ConnectionDirectory):
        self.connections.get_value()

        self.connections.remove(directory)

        self._write()

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

    def _build_ssh_configuration(self, data: dict[str, Any]) -> Optional[SSHTunnelConfiguration]:
        if not data:
            return None

        try:
            return SSHTunnelConfiguration(
                enabled=bool(data.get('enabled')),
                executable=data.get('executable', 'ssh'),
                hostname=data.get('hostname', ''),
                port=int(data.get('port', 22)),
                username=data.get('username', ''),
                password=data.get('password', ''),
                local_port=int(data.get('local_port', 0)),
            )
        except (TypeError, ValueError):
            return None
