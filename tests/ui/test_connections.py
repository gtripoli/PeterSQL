import pytest

from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration

from windows.connections.model import ConnectionModel
from windows.connections import CURRENT_CONNECTION, PENDING_CONNECTION


class TestConnectionModel:
    """Tests for ConnectionModel UI component."""

    @pytest.fixture
    def model(self):
        model = ConnectionModel()
        yield model
        model.clear()

    def test_model_initialization(self, model):
        """Test model initializes with default values."""
        assert model.engine() == "MySQL"
        assert model.port() == 3306
        assert model.ssh_tunnel_enabled() is False
        assert model.ssh_tunnel_port() == 22

    def test_model_clear(self, model):
        """Test model clear resets all values."""
        model.name("Test Connection")
        model.hostname("localhost")
        model.username("root")

        model.clear()

        assert model.name() is None
        assert model.hostname() is None
        assert model.username() is None
        assert model.engine() == "MySQL"
        assert model.port() == 3306

    def test_model_apply_mysql_connection(self, model):
        """Test model apply with MySQL connection."""
        connection = Connection(
            id=1,
            name="MySQL Test",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="db.example.com",
                username="admin",
                password="secret",
                port=3307,
            ),
        )

        model.apply(connection)

        assert model.name() == "MySQL Test"
        assert model.engine() == "MySQL"
        assert model.hostname() == "db.example.com"
        assert model.username() == "admin"
        assert model.password() == "secret"
        assert model.port() == 3307

    def test_model_apply_mariadb_connection(self, model):
        """Test model apply with MariaDB connection."""
        connection = Connection(
            id=2,
            name="MariaDB Test",
            engine=ConnectionEngine.MARIADB,
            configuration=CredentialsConfiguration(
                hostname="mariadb.local",
                username="user",
                password="pass",
                port=3306,
            ),
        )

        model.apply(connection)

        assert model.name() == "MariaDB Test"
        assert model.engine() == "MariaDB"
        assert model.hostname() == "mariadb.local"

    def test_model_apply_sqlite_connection(self, model):
        """Test model apply with SQLite connection."""
        connection = Connection(
            id=3,
            name="SQLite Test",
            engine=ConnectionEngine.SQLITE,
            configuration=SourceConfiguration(
                filename="/path/to/database.db",
            ),
        )

        model.apply(connection)

        assert model.name() == "SQLite Test"
        assert model.engine() == "SQLite"
        assert model.filename() == "/path/to/database.db"

    def test_engine_change_updates_default_port(self, model):
        """Test changing engine updates default port."""
        model.engine("PostgreSQL")
        assert model.port() == 5432

        model.engine("MySQL")
        assert model.port() == 3306

        model.engine("MariaDB")
        assert model.port() == 3306

    def test_model_apply_none_connection(self, model):
        """Test model apply with None connection does nothing."""
        model.name("Existing")
        model.apply(None)
        assert model.name() == "Existing"


class TestConnectionObservables:
    """Tests for connection observables."""

    def test_current_connection_observable(self):
        """Test CURRENT_CONNECTION observable."""
        connection = Connection(
            id=1,
            name="Test",
            engine=ConnectionEngine.MYSQL,
            configuration=CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="",
                port=3306,
            ),
        )

        CURRENT_CONNECTION(connection)
        assert CURRENT_CONNECTION() == connection

        CURRENT_CONNECTION(None)
        assert CURRENT_CONNECTION() is None

    def test_pending_connection_observable(self):
        """Test PENDING_CONNECTION observable."""
        connection = Connection(
            id=2,
            name="Pending",
            engine=ConnectionEngine.SQLITE,
            configuration=SourceConfiguration(filename=":memory:"),
        )

        PENDING_CONNECTION(connection)
        assert PENDING_CONNECTION() == connection

        PENDING_CONNECTION(None)
        assert PENDING_CONNECTION() is None
