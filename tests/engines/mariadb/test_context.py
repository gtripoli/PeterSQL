import pytest


class TestMariaDBContext:
    """Tests for MariaDB context methods."""

    def test_context_connection(self, mariadb_session):
        """Test context is connected."""
        ctx = mariadb_session.context
        assert ctx.is_connected is True

    def test_context_execute_query(self, mariadb_session):
        """Test executing a query."""
        ctx = mariadb_session.context
        ctx.execute("SELECT 1 as test")
        result = ctx.fetchone()
        assert result["test"] == 1

    def test_context_fetchall(self, mariadb_session):
        """Test fetchall method."""
        ctx = mariadb_session.context
        ctx.execute("SELECT 1 as val UNION SELECT 2 UNION SELECT 3")
        results = ctx.fetchall()
        assert len(results) == 3

    def test_context_get_server_version(self, mariadb_session):
        """Test getting server version."""
        version = mariadb_session.context.get_server_version()
        assert version is not None
        assert len(version) > 0

    def test_context_build_sql_safe_name(self, mariadb_session):
        """Test building SQL safe names uses IDENTIFIER_QUOTE."""
        ctx = mariadb_session.context
        quote = ctx.IDENTIFIER_QUOTE

        # Simple names don't need quoting
        assert ctx.build_sql_safe_name("normal") == "normal"
        # Names with spaces are quoted using IDENTIFIER_QUOTE
        assert ctx.build_sql_safe_name("with space") == f'{quote}with space{quote}'

    def test_context_transaction(self, mariadb_session, mariadb_database):
        """Test transaction context manager."""
        ctx = mariadb_session.context
        db_name = mariadb_database.name

        ctx.execute(f"CREATE TABLE {db_name}.test_tx (id INT PRIMARY KEY, name VARCHAR(50))")

        with ctx.transaction() as tx:
            tx.execute(f"INSERT INTO {db_name}.test_tx (id, name) VALUES (1, 'test')")

        ctx.execute(f"SELECT COUNT(*) as cnt FROM {db_name}.test_tx")
        assert ctx.fetchone()["cnt"] == 1

        ctx.execute(f"DROP TABLE {db_name}.test_tx")

    def test_context_databases_list(self, mariadb_session):
        """Test getting databases list."""
        ctx = mariadb_session.context
        databases = ctx.databases.get_value()
        assert len(databases) > 0
        # Should have at least information_schema
        db_names = [db.name for db in databases]
        assert "information_schema" in db_names
