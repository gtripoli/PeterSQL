import pytest


class TestPostgreSQLContext:
    """Tests for PostgreSQL context - focus on reading database structures."""

    def test_context_connection(self, postgresql_session):
        """Test context is connected."""
        ctx = postgresql_session.context
        assert ctx.is_connected is True

    def test_context_execute_query(self, postgresql_session):
        """Test executing a simple query."""
        ctx = postgresql_session.context
        ctx.execute("SELECT 1 as test")
        result = ctx.fetchone()
        assert result["test"] == 1

    def test_context_fetchall(self, postgresql_session):
        """Test fetchall method."""
        ctx = postgresql_session.context
        ctx.execute("SELECT 1 as val UNION SELECT 2 UNION SELECT 3")
        results = ctx.fetchall()
        assert len(results) == 3

    def test_context_get_server_version(self, postgresql_session):
        """Test getting server version."""
        version = postgresql_session.context.get_server_version()
        assert version is not None
        assert "PostgreSQL" in version

    def test_context_get_server_uptime(self, postgresql_session):
        """Test getting server uptime."""
        uptime = postgresql_session.context.get_server_uptime()
        assert uptime is not None
        assert uptime >= 0

    def test_context_build_sql_safe_name(self, postgresql_session):
        """Test building SQL safe names uses QUOTE_IDENTIFIER."""
        ctx = postgresql_session.context
        quote = ctx.QUOTE_IDENTIFIER

        assert quote == '"'
        assert ctx.build_sql_safe_name("normal") == "normal"
        assert ctx.build_sql_safe_name("with space") == f'{quote}with space{quote}'

    def test_context_databases_list(self, postgresql_session):
        """Test reading databases list from server."""
        ctx = postgresql_session.context
        databases = ctx.databases.get_value()
        assert len(databases) > 0
        db_names = [db.name for db in databases]
        assert "postgres" in db_names

    def test_context_collations_loaded(self, postgresql_session):
        """Test collations are loaded from server."""
        ctx = postgresql_session.context
        assert len(ctx.COLLATIONS) > 0

    def test_context_keywords_loaded(self, postgresql_session):
        """Test keywords are loaded from server."""
        ctx = postgresql_session.context
        assert len(ctx.KEYWORDS) > 0
        keywords_lower = [k.lower() for k in ctx.KEYWORDS]
        assert "select" in keywords_lower

    def test_context_functions_loaded(self, postgresql_session):
        """Test functions are loaded from server."""
        ctx = postgresql_session.context
        assert len(ctx.FUNCTIONS) > 0
