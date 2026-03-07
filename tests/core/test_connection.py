from structures.connection import Connection, ConnectionEngine
from structures.configurations import (
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)


class TestConnection:
    def test_connection_mysql(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="secret",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="MySQL Test",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        assert connection.id == 1
        assert connection.name == "MySQL Test"
        assert connection.engine == ConnectionEngine.MYSQL
        assert connection.configuration.hostname == "localhost"
        assert connection.configuration.port == 3306

    def test_connection_sqlite(self):
        config = SourceConfiguration(filename=":memory:")
        connection = Connection(
            id=2,
            name="SQLite Test",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert connection.engine == ConnectionEngine.SQLITE
        assert connection.configuration.filename == ":memory:"

    def test_connection_is_new(self):
        config = SourceConfiguration(filename=":memory:")
        connection = Connection(
            id=-1,
            name="New",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert connection.is_new is True

    def test_connection_is_not_new(self):
        config = SourceConfiguration(filename=":memory:")
        connection = Connection(
            id=0,
            name="Existing",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )

        assert connection.is_new is False

    def test_connection_copy(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="Original",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        copy = connection.copy()

        assert copy.id == connection.id
        assert copy.name == connection.name
        assert copy is not connection

    def test_connection_to_dict(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="secret",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="Test",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        data = connection.to_dict()

        assert data["id"] == 1
        assert data["name"] == "Test"
        assert data["engine"] == "MySQL"
        assert data["configuration"]["hostname"] == "localhost"

    def test_connection_with_ssh_tunnel(self):
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
        connection = Connection(
            id=1,
            name="With SSH",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
            ssh_tunnel=ssh,
        )

        assert connection.ssh_tunnel is not None
        assert connection.ssh_tunnel.enabled is True
        assert connection.ssh_tunnel.hostname == "bastion.example.com"

    def test_connection_is_valid_with_empty_password(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="Local",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        assert connection.is_valid is True

    def test_record_connection_attempt_success_updates_statistics(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="Stats Success",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )

        connection.record_connection_attempt(
            timestamp="2026-03-07 17:00:00",
            success=True,
            duration_ms=120,
        )

        assert connection.total_connection_attempts == 1
        assert connection.successful_connections == 1
        assert connection.unsuccessful_connections == 0
        assert connection.last_connection_at == "2026-03-07 17:00:00"
        assert connection.last_successful_connection_at == "2026-03-07 17:00:00"
        assert connection.last_failure_reason is None
        assert connection.most_recent_connection_duration_ms == 120
        assert connection.average_connection_time_ms == 120

    def test_record_connection_attempt_failure_updates_statistics(self):
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password="",
            port=3306,
        )
        connection = Connection(
            id=1,
            name="Stats Failure",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
            average_connection_time_ms=100,
            total_connection_attempts=1,
            successful_connections=1,
        )

        connection.record_connection_attempt(
            timestamp="2026-03-07 17:01:00",
            success=False,
            duration_ms=300,
            failure_reason="Authentication failed",
        )

        assert connection.total_connection_attempts == 2
        assert connection.successful_connections == 1
        assert connection.unsuccessful_connections == 1
        assert connection.last_connection_at == "2026-03-07 17:01:00"
        assert connection.last_successful_connection_at is None
        assert connection.last_failure_reason == "Authentication failed"
        assert connection.most_recent_connection_duration_ms == 300
        assert connection.average_connection_time_ms == 200


class TestConnectionEngine:
    def test_engine_mysql(self):
        engine = ConnectionEngine.MYSQL
        assert engine.value.name == "MySQL"

    def test_engine_mariadb(self):
        engine = ConnectionEngine.MARIADB
        assert engine.value.name == "MariaDB"

    def test_engine_sqlite(self):
        engine = ConnectionEngine.SQLITE
        assert engine.value.name == "SQLite"

    def test_engine_postgresql(self):
        engine = ConnectionEngine.POSTGRESQL
        assert engine.value.name == "PostgreSQL"

    def test_engine_from_name_mysql(self):
        engine = ConnectionEngine.from_name("MySQL")
        assert engine == ConnectionEngine.MYSQL

    def test_engine_from_name_sqlite(self):
        engine = ConnectionEngine.from_name("SQLite")
        assert engine == ConnectionEngine.SQLITE

    def test_engine_from_name_case_insensitive(self):
        engine = ConnectionEngine.from_name("MariaDB")
        assert engine == ConnectionEngine.MARIADB


class TestCredentialsConfiguration:
    def test_credentials_config(self):
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
    def test_source_config(self):
        config = SourceConfiguration(filename="/path/to/database.db")

        assert config.filename == "/path/to/database.db"

    def test_source_config_memory(self):
        config = SourceConfiguration(filename=":memory:")

        assert config.filename == ":memory:"
