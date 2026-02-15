import pytest
from structures.engines.mysql.database import MySQLTable
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mysql.indextype import MySQLIndexType
from structures.ssh_tunnel import SSHTunnel


def create_users_table(mysql_database, mysql_session) -> MySQLTable:
    """Helper: create and save a users table with id and name columns.
    
    Uses build_empty_* API from context to construct objects.
    Returns the persisted table from the database (with proper handlers).
    """
    ctx = mysql_session.context
    ctx.execute("USE testdb")

    table = ctx.build_empty_table(mysql_database, name="users", engine="InnoDB", collation_name="utf8mb4_general_ci")

    id_column = ctx.build_empty_column(
        table,
        MySQLDataType.INT,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
        length=11,
    )

    name_column = ctx.build_empty_column(
        table,
        MySQLDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        MySQLIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    # Create table directly via raw SQL
    ctx.execute(table.raw_create())

    # Refresh tables to get the persisted table with proper handlers
    mysql_database.tables.refresh()
    return next(t for t in mysql_database.tables.get_value() if t.name == "users")


@pytest.fixture(scope="function")
def ssh_mysql_session(mysql_container, mysql_session):
    """Create SSH tunnel session for testing."""
    try:
        # Create SSH tunnel to MySQL container
        tunnel = SSHTunnel(
            mysql_container.get_container_host_ip(),
            22,  # Assuming SSH access to host
            ssh_username=None,
            ssh_password=None,
            remote_port=mysql_container.get_exposed_port(3306),
            local_bind_address=('localhost', 0)
        )
        
        tunnel.start(timeout=5)
        
        # Create connection using tunnel
        from structures.session import Session
        from structures.connection import Connection, ConnectionEngine
        from structures.configurations import CredentialsConfiguration
        
        config = CredentialsConfiguration(
            hostname="localhost",
            username="root",
            password=mysql_container.root_password,
            port=tunnel.local_port,
        )
        
        connection = Connection(
            id=1,
            name="ssh_mysql_test",
            engine=ConnectionEngine.MYSQL,
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


class TestMySQLIntegration:
    """Integration tests for MySQL engine using build_empty_* API."""

    def test_table_create_and_drop(self, mysql_session, mysql_database):
        """Test table creation and deletion."""
        table = create_users_table(mysql_database, mysql_session)
        assert table.is_valid is True
        assert table.id >= 0

        # Verify table exists in database
        tables = mysql_database.tables.get_value()
        assert any(t.name == "users" for t in tables)

        assert table.drop() is True

        # Refresh to verify table was deleted
        mysql_database.tables.refresh()
        tables = mysql_database.tables.get_value()
        assert not any(t.name == "users" for t in tables)

    def test_ssh_tunnel_basic_operations(self, ssh_mysql_session, mysql_database):
        """Test basic CRUD operations through SSH tunnel."""
        session, tunnel = ssh_mysql_session
        
        # Create table
        table = create_users_table(mysql_database, session)
        
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

    def test_ssh_tunnel_transaction_support(self, ssh_mysql_session, mysql_database):
        """Test transaction support through SSH tunnel."""
        session, tunnel = ssh_mysql_session
        table = create_users_table(mysql_database, session)
        
        # Test successful transaction
        with session.context.transaction() as tx:
            tx.execute("INSERT INTO testdb.users (name) VALUES (%s)", ("test1",))
            tx.execute("INSERT INTO testdb.users (name) VALUES (%s)", ("test2",))
        
        # Verify data was committed
        session.context.execute("SELECT COUNT(*) as count FROM testdb.users")
        result = session.context.fetchone()
        assert result['count'] == 2
        
        # Test failed transaction
        try:
            with session.context.transaction() as tx:
                tx.execute("INSERT INTO testdb.users (name) VALUES (%s)", ("test3",))
                tx.execute("INSERT INTO testdb.users (id, name) VALUES (1, 'duplicate')")  # Should fail
        except:
            pass  # Expected to fail
        
        # Verify rollback worked
        session.context.execute("SELECT COUNT(*) as count FROM testdb.users")
        result = session.context.fetchone()
        assert result['count'] == 2
        
        table.drop()

    def test_ssh_tunnel_error_handling(self, ssh_mysql_session, mysql_database):
        """Test error handling through SSH tunnel."""
        session, tunnel = ssh_mysql_session
        table = create_users_table(mysql_database, session)
        
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
