from structures.engines.postgresql.database import PostgreSQLTable
from structures.engines.postgresql.datatype import PostgreSQLDataType
from structures.engines.postgresql.indextype import PostgreSQLIndexType


def create_users_table(postgresql_database, postgresql_session) -> PostgreSQLTable:
    """Helper: create and save a users table with id and name columns.
    
    Uses build_empty_* API from context to construct objects.
    Returns the persisted table from the database (with proper handlers).
    """
    ctx = postgresql_session.context

    table = ctx.build_empty_table(postgresql_database, name="users", schema="public")

    id_column = ctx.build_empty_column(
        table,
        PostgreSQLDataType.SERIAL,
        name="id",
        is_nullable=False,
    )

    name_column = ctx.build_empty_column(
        table,
        PostgreSQLDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        PostgreSQLIndexType.PRIMARY,
        ["id"],
        name="users_pkey",
    )
    table.indexes.append(primary_index)

    # Create table directly via raw SQL
    ctx.execute(table.raw_create())

    # Refresh tables to get the persisted table with proper handlers
    postgresql_database.tables.refresh()
    return next(t for t in postgresql_database.tables.get_value() if t.name == "users")


class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL engine using build_empty_* API."""

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
        assert ctx.IDENTIFIER_QUOTE == '"'
