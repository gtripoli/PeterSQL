import pytest

from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration


class TestConnection:
    """Tests for Connection dataclass."""

    def test_connection_mysql(self):
        """Test MySQL connection creation."""
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="secret",
            port=3306,
        )
        conn = Connection(
            id=1,
            name="MySQL Test",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        assert conn.id == 1
        assert conn.name == "MySQL Test"
        assert conn.engine == ConnectionEngine.MYSQL
        assert conn.configuration.hostname == "localhost"
        assert conn.configuration.port == 3306

    def test_connection_sqlite(self):
        """Test SQLite connection creation."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(
            id=2,
            name="SQLite Test",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert conn.engine == ConnectionEngine.SQLITE
        assert conn.configuration.filename == ":memory:"

    def test_connection_is_new(self):
        """Test is_new property."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(
            id=-1,
            name="New",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert conn.is_new is True

    def test_connection_is_not_new(self):
        """Test is_new property when id >= 0."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(
            id=0,
            name="Existing",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert conn.is_new is False

    def test_connection_copy(self):
        """Test connection copy."""
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        conn = Connection(
            id=1,
            name="Original",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        copy = conn.copy()

        assert copy.id == conn.id
        assert copy.name == conn.name
        assert copy is not conn

    def test_connection_to_dict(self):
        """Test connection serialization to dict."""
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="secret",
            port=3306,
        )
        conn = Connection(
            id=1,
            name="Test",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        d = conn.to_dict()

        assert d["id"] == 1
        assert d["name"] == "Test"
        assert d["engine"] == "MySQL"
        assert d["configuration"]["hostname"] == "localhost"

    def test_connection_with_ssh_tunnel(self):
        """Test connection with SSH tunnel."""
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        ssh = SSHTunnelConfiguration(
            enabled=True,
            executable="ssh",
            hostname="bastion.example.com",
            port=22,
            username="admin",
            password="sshpass",
            local_port=3307,
        )
        conn = Connection(
            id=1,
            name="With SSH",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
            ssh_tunnel=ssh,
        )

        assert conn.ssh_tunnel is not None
        assert conn.ssh_tunnel.enabled is True
        assert conn.ssh_tunnel.hostname == "bastion.example.com"


class TestConnectionEngine:
    """Tests for ConnectionEngine enum."""

    def test_engine_mysql(self):
        """Test MySQL engine."""
        engine = ConnectionEngine.MYSQL
        assert engine.value.name == "MySQL"

    def test_engine_mariadb(self):
        """Test MariaDB engine."""
        engine = ConnectionEngine.MARIADB
        assert engine.value.name == "MariaDB"

    def test_engine_sqlite(self):
        """Test SQLite engine."""
        engine = ConnectionEngine.SQLITE
        assert engine.value.name == "SQLite"

    def test_engine_postgresql(self):
        """Test PostgreSQL engine."""
        engine = ConnectionEngine.POSTGRESQL
        assert engine.value.name == "PostgreSQL"

    def test_engine_from_name_mysql(self):
        """Test from_name with MySQL."""
        engine = ConnectionEngine.from_name("MySQL")
        assert engine == ConnectionEngine.MYSQL

    def test_engine_from_name_sqlite(self):
        """Test from_name with SQLite."""
        engine = ConnectionEngine.from_name("SQLite")
        assert engine == ConnectionEngine.SQLITE

    def test_engine_from_name_case_insensitive(self):
        """Test from_name is case sensitive."""
        engine = ConnectionEngine.from_name("MariaDB")
        assert engine == ConnectionEngine.MARIADB


class TestCredentialsConfiguration:
    """Tests for CredentialsConfiguration."""

    def test_credentials_config(self):
        """Test credentials configuration."""
        config = CredentialsConfiguration(
            hostname="db.example.com",
            username="admin",
            password="secret123",
            port=3306,
        )

        assert config.hostname == "db.example.com"
        assert config.username == "admin"
        assert config.password == "secret123"
        assert config.port == 3306


class TestSourceConfiguration:
    """Tests for SourceConfiguration."""

    def test_source_config(self):
        """Test source configuration."""
        config = SourceConfiguration(filename="/path/to/database.db")

        assert config.filename == "/path/to/database.db"

    def test_source_config_memory(self):
        """Test source configuration with memory."""
        config = SourceConfiguration(filename=":memory:")

        assert config.filename == ":memory:"
