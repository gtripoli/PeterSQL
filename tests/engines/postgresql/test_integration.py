import pytest
from structures.engines.postgresql.database import PostgreSQLTable
from structures.engines.postgresql.datatype import PostgreSQLDataType
from structures.engines.postgresql.indextype import PostgreSQLIndexType
from structures.ssh_tunnel import SSHTunnel


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


@pytest.fixture(scope="function")
def ssh_postgresql_session(postgresql_container, postgresql_session):
    """Create SSH tunnel session for testing."""
    try:
        # Create SSH tunnel to PostgreSQL container
        tunnel = SSHTunnel(
            postgresql_container.get_container_host_ip(),
            22,  # Assuming SSH access to host
            ssh_username=None,
            ssh_password=None,
            remote_port=postgresql_container.get_exposed_port(5432),
            local_bind_address=('localhost', 0)
        )
        
        tunnel.start(timeout=5)
        
        # Create connection using tunnel
        from structures.session import Session
        from structures.connection import Connection, ConnectionEngine
        from structures.configurations import CredentialsConfiguration
        
        config = CredentialsConfiguration(
            hostname="localhost",
            username=postgresql_container.username,
            password=postgresql_container.password,
            port=tunnel.local_port,
        )
        
        connection = Connection(
            id=1,
            name="ssh_postgresql_test",
            engine=ConnectionEngine.POSTGRESQL,
            configuration=config,
        )
        
        session = Session(connection=connection)
        session.connect()
        
        yield session, tunnel
        
    except Exception:
        pytest.skip("SSH tunnel not available")
        
    finally:
        try:
            session.disconnect()
        except:
            pass
        try:
            tunnel.stop()
        except:
            pass


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

    def test_ssh_tunnel_basic_operations(self, ssh_postgresql_session, postgresql_database):
        """Test basic CRUD operations through SSH tunnel."""
        session, tunnel = ssh_postgresql_session
        
        # Create table
        table = create_users_table(postgresql_database, session)
        
        # Test INSERT
        record = session.context.build_empty_record(table, values={"name": "John Doe"})
        assert record.insert() is True
        
        # Test SELECT
        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "John Doe"
        
        # Test UPDATE
        record = records[0]
        record.values["name"] = "Jane Doe"
        assert record.update() is True
        
        # Verify UPDATE
        table.load_records()
        records = table.records.get_value()
        assert records[0].values["name"] == "Jane Doe"
        
        # Test DELETE
        assert record.delete() is True
        
        # Verify DELETE
        table.load_records()
        assert len(table.records.get_value()) == 0
        
        table.drop()

    def test_ssh_tunnel_transaction_support(self, ssh_postgresql_session, postgresql_database):
        """Test transaction support through SSH tunnel."""
        session, tunnel = ssh_postgresql_session
        table = create_users_table(postgresql_database, session)
        
        # Test successful transaction
        with session.context.transaction() as tx:
            tx.execute("INSERT INTO public.users (name) VALUES (%s)", ("test1",))
            tx.execute("INSERT INTO public.users (name) VALUES (%s)", ("test2",))
        
        # Verify data was committed
        session.context.execute("SELECT COUNT(*) as count FROM public.users")
        result = session.context.fetchone()
        assert result['count'] == 2
        
        # Test failed transaction
        try:
            with session.context.transaction() as tx:
                tx.execute("INSERT INTO public.users (name) VALUES (%s)", ("test3",))
                tx.execute("INVALID SQL")  # Should fail
        except:
            pass  # Expected to fail
        
        # Verify rollback worked
        session.context.execute("SELECT COUNT(*) as count FROM public.users")
        result = session.context.fetchone()
        assert result['count'] == 2
        
        table.drop()

    def test_ssh_tunnel_error_handling(self, ssh_postgresql_session, postgresql_database):
        """Test error handling through SSH tunnel."""
        session, tunnel = ssh_postgresql_session
        table = create_users_table(postgresql_database, session)
        
        # Test invalid SQL
        try:
            session.context.execute("INVALID SQL QUERY")
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected
        
        # Test connection is still working
        result = session.context.execute("SELECT 1 as test")
        assert result is True
        
        table.drop()

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
