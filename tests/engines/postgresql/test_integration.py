import pytest


class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL engine - reading existing structures."""

    def test_read_system_tables(self, postgresql_session):
        """Test reading system tables from postgres database."""
        ctx = postgresql_session.context
        databases = ctx.databases.get_value()

        postgres_db = next((db for db in databases if db.name == "postgres"), None)
        assert postgres_db is not None

        # PostgreSQL has system tables in pg_catalog schema
        tables = ctx.get_tables(postgres_db)
        # postgres database may have no user tables, that's ok
        assert isinstance(tables, list)

    def test_read_database_properties(self, postgresql_session):
        """Test reading database properties."""
        ctx = postgresql_session.context
        databases = ctx.databases.get_value()

        for db in databases:
            assert db.id is not None
            assert db.name is not None
            assert db.total_bytes >= 0
            assert db.context == ctx

    def test_read_views_from_database(self, postgresql_session):
        """Test reading views from database."""
        ctx = postgresql_session.context
        databases = ctx.databases.get_value()

        postgres_db = next((db for db in databases if db.name == "postgres"), None)
        assert postgres_db is not None

        views = ctx.get_views(postgres_db)
        assert isinstance(views, list)

    def test_read_triggers_from_database(self, postgresql_session):
        """Test reading triggers from database."""
        ctx = postgresql_session.context
        databases = ctx.databases.get_value()

        postgres_db = next((db for db in databases if db.name == "postgres"), None)
        assert postgres_db is not None

        triggers = ctx.get_triggers(postgres_db)
        assert isinstance(triggers, list)

    def test_datatype_class(self, postgresql_session):
        """Test PostgreSQL datatype class is properly configured."""
        ctx = postgresql_session.context
        datatype_class = ctx.DATATYPE

        all_types = datatype_class.get_all()
        assert len(all_types) > 0

        type_names = [t.name.lower() for t in all_types]
        assert "integer" in type_names or "int4" in type_names
        assert "text" in type_names
        assert "boolean" in type_names or "bool" in type_names

    def test_indextype_class(self, postgresql_session):
        """Test PostgreSQL indextype class is properly configured."""
        ctx = postgresql_session.context
        indextype_class = ctx.INDEXTYPE

        all_types = indextype_class.get_all()
        assert len(all_types) > 0

    def test_quote_identifier(self, postgresql_session):
        """Test PostgreSQL uses double quotes for identifiers."""
        ctx = postgresql_session.context
        assert ctx.QUOTE_IDENTIFIER == '"'
