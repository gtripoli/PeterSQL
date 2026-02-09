import os
import tempfile
import pytest

from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration

from windows.connections import ConnectionDirectory
from windows.connections.repository import ConnectionsRepository


class TestConnectionsRepository:
    """Tests for ConnectionsRepository."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        fd, path = tempfile.mkstemp(suffix=".yml")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def repository(self, temp_config_file):
        """Create a repository with temporary config file."""
        return ConnectionsRepository(config_file=temp_config_file)

    def test_repository_initialization(self, repository):
        """Test repository initializes with empty connections."""
        connections = repository.connections.get_value()
        assert connections == []

    def test_add_mysql_connection(self, repository):
        """Test adding a MySQL connection."""
        connection = Connection(
            id=-1,
            name="MySQL Test",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="secret",
                port=3306,
            ),
        )

        connection_id = repository.add_connection(connection)
        assert connection_id >= 0

        connections = repository.connections.get_value()
        assert len(connections) == 1
        assert connections[0].name == "MySQL Test"
        assert connections[0].engine == ConnectionEngine.MYSQL

    def test_add_sqlite_connection(self, repository):
        """Test adding a SQLite connection."""
        connection = Connection(
            id=-1,
            name="SQLite Test",
            engine=ConnectionEngine.SQLITE,
            configuration=SourceConfiguration(filename="/path/to/db.sqlite"),
        )

        connection_id = repository.add_connection(connection)
        assert connection_id >= 0

        connections = repository.connections.get_value()
        assert len(connections) == 1
        assert connections[0].name == "SQLite Test"
        assert connections[0].engine == ConnectionEngine.SQLITE

    def test_add_multiple_connections(self, repository):
        """Test adding multiple connections."""
        conn1 = Connection(
            id=-1,
            name="Connection 1",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="host1", username="user1", password="pass1", port=3306
            ),
        )
        conn2 = Connection(
            id=-1,
            name="Connection 2",
            engine=ConnectionEngine.MARIADB,
            configuration=CredentialsConfiguration(
                hostname="host2", username="user2", password="pass2", port=3306
            ),
        )

        repository.add_connection(conn1)
        repository.add_connection(conn2)

        connections = repository.connections.get_value()
        assert len(connections) == 2

    def test_save_connection(self, repository):
        """Test saving/updating a connection."""
        connection = Connection(
            id=-1,
            name="Original Name",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost", username="root", password="", port=3306
            ),
        )

        connection_id = repository.add_connection(connection)

        connection.name = "Updated Name"
        repository.save_connection(connection)

        connections = repository.connections.get_value()
        assert connections[0].name == "Updated Name"

    def test_delete_connection(self, repository):
        """Test deleting a connection."""
        connection = Connection(
            id=-1,
            name="To Delete",
            engine=ConnectionEngine.SQLITE,
            configuration=SourceConfiguration(filename=":memory:"),
        )

        repository.add_connection(connection)
        assert len(repository.connections.get_value()) == 1

        repository.delete_connection(connection)
        assert len(repository.connections.get_value()) == 0

    def test_add_directory(self, repository):
        """Test adding a directory."""
        directory = ConnectionDirectory(name="Production", children=[])

        repository.add_directory(directory)

        items = repository.connections.get_value()
        assert len(items) == 1
        assert isinstance(items[0], ConnectionDirectory)
        assert items[0].name == "Production"

    def test_add_connection_to_directory(self, repository):
        """Test adding a connection inside a directory."""
        directory = ConnectionDirectory(name="Development", children=[])
        repository.add_directory(directory)

        connection = Connection(
            id=-1,
            name="Dev MySQL",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="dev.local", username="dev", password="dev", port=3306
            ),
        )

        repository.add_connection(connection, parent=directory)

        items = repository.connections.get_value()
        assert len(items) == 1
        assert len(items[0].children) == 1
        assert items[0].children[0].name == "Dev MySQL"

    def test_delete_directory(self, repository):
        """Test deleting a directory."""
        directory = ConnectionDirectory(name="To Delete", children=[])
        repository.add_directory(directory)

        assert len(repository.connections.get_value()) == 1

        repository.delete_directory(directory)
        assert len(repository.connections.get_value()) == 0

    def test_persistence(self, temp_config_file):
        """Test that connections persist across repository instances."""
        repo1 = ConnectionsRepository(config_file=temp_config_file)

        connection = Connection(
            id=-1,
            name="Persistent",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost", username="root", password="", port=3306
            ),
        )
        repo1.add_connection(connection)

        repo2 = ConnectionsRepository(config_file=temp_config_file)
        connections = repo2.connections.get_value()

        assert len(connections) == 1
        assert connections[0].name == "Persistent"
