from structures.engines.mariadb.database import MariaDBTable
from structures.engines.mariadb.datatype import MariaDBDataType
from structures.engines.mariadb.indextype import MariaDBIndexType


def create_users_table(mariadb_database, mariadb_session) -> MariaDBTable:
    """Helper: create and save a users table with id and name columns.
    
    Uses build_empty_* API from context to construct objects.
    Returns the persisted table from the database (with proper handlers).
    """
    ctx = mariadb_session.context
    ctx.execute("USE testdb")

    table = ctx.build_empty_table(mariadb_database, name="users", engine="InnoDB", collation_name="utf8mb4_general_ci")

    id_column = ctx.build_empty_column(
        table,
        MariaDBDataType.INT,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
        length=11,
    )

    name_column = ctx.build_empty_column(
        table,
        MariaDBDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        MariaDBIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    # Create table directly via raw SQL
    ctx.execute(table.raw_create())

    # Refresh tables to get the persisted table with proper handlers
    mariadb_database.tables.refresh()
    return next(t for t in mariadb_database.tables.get_value() if t.name == "users")


class TestMariaDBIntegration:
    """Integration tests for MariaDB engine using build_empty_* API."""

    def test_table_create_and_drop(self, mariadb_session, mariadb_database):
        """Test table creation and deletion."""
        table = create_users_table(mariadb_database, mariadb_session)
        assert table.is_valid is True
        assert table.id >= 0

        # Verify table exists in database
        tables = mariadb_database.tables.get_value()
        assert any(t.name == "users" for t in tables)

        assert table.drop() is True

        # Refresh to verify table was deleted
        mariadb_database.tables.refresh()
        tables = mariadb_database.tables.get_value()
        assert not any(t.name == "users" for t in tables)

    def test_record_insert(self, mariadb_session, mariadb_database):
        """Test record insertion."""
        table = create_users_table(mariadb_database, mariadb_session)

        table.load_records()
        assert len(table.records.get_value()) == 0

        record = mariadb_session.context.build_empty_record(table, values={"name": "John Doe"})
        assert record.insert() is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "John Doe"

        table.drop()

    def test_record_update(self, mariadb_session, mariadb_database):
        """Test record update."""
        table = create_users_table(mariadb_database, mariadb_session)
        table.load_records()

        record = mariadb_session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        record = table.records.get_value()[0]
        assert record.is_valid() is True
        assert record.is_new() is False

        record.values["name"] = "Jane Doe"
        assert record.update() is True

        table.load_records()
        records = table.records.get_value()
        assert records[0].values["name"] == "Jane Doe"

        table.drop()

    def test_record_delete(self, mariadb_session, mariadb_database):
        """Test record deletion."""
        table = create_users_table(mariadb_database, mariadb_session)
        table.load_records()

        record = mariadb_session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        record = table.records.get_value()[0]
        assert record.delete() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()

    def test_column_add(self, mariadb_session, mariadb_database):
        """Test adding a column to an existing table."""
        table = create_users_table(mariadb_database, mariadb_session)

        email_column = mariadb_session.context.build_empty_column(
            table,
            MariaDBDataType.VARCHAR,
            name="email",
            is_nullable=True,
            length=255,
        )
        assert email_column.add() is True

        # Refresh columns to verify column was added
        table.columns.refresh()
        columns = table.columns.get_value()
        assert any(c.name == "email" for c in columns)

        table.drop()

    def test_table_truncate(self, mariadb_session, mariadb_database):
        """Test table truncation."""
        table = create_users_table(mariadb_database, mariadb_session)
        table.load_records()

        record = mariadb_session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        assert len(table.records.get_value()) == 1

        assert table.truncate() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()

    def test_index_create_and_drop(self, mariadb_session, mariadb_database):
        """Test index creation and deletion."""
        table = create_users_table(mariadb_database, mariadb_session)

        idx_name = mariadb_session.context.build_empty_index(
            table,
            MariaDBIndexType.INDEX,
            ["name"],
            name="idx_name",
        )
        assert idx_name.create() is True

        # Refresh indexes to verify index was created
        table.indexes.refresh()
        indexes = table.indexes.get_value()
        assert any(i.name == "idx_name" for i in indexes)

        assert idx_name.drop() is True

        # Refresh indexes to verify index was deleted
        table.indexes.refresh()
        indexes = table.indexes.get_value()
        assert not any(i.name == "idx_name" for i in indexes)

        table.drop()

    def test_view_create_and_drop(self, mariadb_session, mariadb_database):
        """Test view creation and deletion."""
        table = create_users_table(mariadb_database, mariadb_session)

        view = mariadb_session.context.build_empty_view(
            mariadb_database,
            name="active_users_view",
            sql="SELECT * FROM testdb.users WHERE name IS NOT NULL",
        )
        assert view.create() is True

        # Refresh views to verify view was created
        mariadb_database.views.refresh()
        views = mariadb_database.views.get_value()
        assert any(v.name == "active_users_view" for v in views)

        assert view.drop() is True

        # Refresh views to verify view was deleted
        mariadb_database.views.refresh()
        views = mariadb_database.views.get_value()
        assert not any(v.name == "active_users_view" for v in views)

        table.drop()

    def test_trigger_create_and_drop(self, mariadb_session, mariadb_database):
        """Test trigger creation and deletion."""
        table = create_users_table(mariadb_database, mariadb_session)

        trigger = mariadb_session.context.build_empty_trigger(
            mariadb_database,
            name="trg_users_insert",
            sql="AFTER INSERT ON testdb.users FOR EACH ROW BEGIN END",
        )
        assert trigger.create() is True

        # Refresh triggers to verify trigger was created
        mariadb_database.triggers.refresh()
        triggers = mariadb_database.triggers.get_value()
        assert any(t.name == "trg_users_insert" for t in triggers)

        assert trigger.drop() is True

        # Refresh triggers to verify trigger was deleted
        mariadb_database.triggers.refresh()
        triggers = mariadb_database.triggers.get_value()
        assert not any(t.name == "trg_users_insert" for t in triggers)

        table.drop()
