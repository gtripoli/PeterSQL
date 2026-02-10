from structures.engines.sqlite.database import (
    SQLiteTable,
    SQLiteColumn,
    SQLiteIndex,
    SQLiteRecord,
    SQLiteView,
    SQLiteTrigger,
)
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


def create_users_table(sqlite_database, sqlite_session) -> SQLiteTable:
    """Helper: create and save a users table with id and name columns.
    
    Uses build_empty_* API from context to construct objects.
    Returns the persisted table from the database (with proper handlers).
    """
    ctx = sqlite_session.context

    table = ctx.build_empty_table(sqlite_database, name="users")

    id_column = ctx.build_empty_column(
        table,
        SQLiteDataType.INTEGER,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
    )

    name_column = ctx.build_empty_column(
        table,
        SQLiteDataType.TEXT,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        SQLiteIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    # save() calls create() + database.refresh()
    table.save()

    # Explicitly refresh tables to get the persisted table with proper handlers
    sqlite_database.tables.refresh()
    return next(t for t in sqlite_database.tables.get_value() if t.name == "users")


class TestSQLiteIntegration:
    """Integration tests for SQLite engine."""

    def test_table_create_and_drop(self, sqlite_session, sqlite_database):
        """Test table creation and deletion."""
        # create_users_table uses save() which creates and refreshes
        table = create_users_table(sqlite_database, sqlite_session)
        assert table.is_valid is True
        assert table.id >= 0  # ID should be assigned after save (0-indexed)

        # Verify table exists in database
        tables = sqlite_database.tables.get_value()
        assert any(t.name == "users" for t in tables)

        assert table.drop() is True

        # Refresh to verify table was deleted
        sqlite_database.tables.refresh()
        tables = sqlite_database.tables.get_value()
        assert not any(t.name == "users" for t in tables)

    def test_record_insert(self, sqlite_session, sqlite_database):
        """Test record insertion."""
        table = create_users_table(sqlite_database, sqlite_session)

        table.load_records()
        assert len(table.records.get_value()) == 0

        record = sqlite_session.context.build_empty_record(table, values={"name": "John Doe"})
        assert record.insert() is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "John Doe"

        table.drop()

    def test_record_update(self, sqlite_session, sqlite_database):
        """Test record update."""
        table = create_users_table(sqlite_database, sqlite_session)
        table.load_records()  # Initialize records before build_empty_record

        record = sqlite_session.context.build_empty_record(table, values={"name": "John Doe"})
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

    def test_record_delete(self, sqlite_session, sqlite_database):
        """Test record deletion."""
        table = create_users_table(sqlite_database, sqlite_session)
        table.load_records()  # Initialize records before build_empty_record

        record = sqlite_session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        record = table.records.get_value()[0]
        assert record.delete() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()

    def test_column_add(self, sqlite_session, sqlite_database):
        """Test adding a column to an existing table."""
        table = create_users_table(sqlite_database, sqlite_session)

        email_column = sqlite_session.context.build_empty_column(
            table,
            SQLiteDataType.TEXT,
            name="email",
            is_nullable=True,
        )
        assert email_column.add() is True

        # Refresh columns to verify column was added
        table.columns.refresh()
        columns = table.columns.get_value()
        assert any(c.name == "email" for c in columns)

        table.drop()

    def test_column_rename(self, sqlite_session, sqlite_database):
        """Test renaming a column."""
        table = create_users_table(sqlite_database, sqlite_session)

        # Add a column to rename
        email_column = sqlite_session.context.build_empty_column(
            table,
            SQLiteDataType.TEXT,
            name="email",
            is_nullable=True,
        )
        assert email_column.add() is True

        # Refresh columns to get the persisted column
        table.columns.refresh()
        email_column = next(c for c in table.columns.get_value() if c.name == "email")

        # Rename the column
        assert email_column.rename("user_email") is True

        # Refresh columns to verify rename
        table.columns.refresh()
        columns = table.columns.get_value()
        assert any(c.name == "user_email" for c in columns)
        assert not any(c.name == "email" for c in columns)

        table.drop()

    def test_column_with_check_constraint(self, sqlite_session, sqlite_database):
        """Test column with CHECK constraint."""
        table = create_users_table(sqlite_database, sqlite_session)
        table.load_records()  # Initialize records before build_empty_record
        ctx = sqlite_session.context

        email_column = ctx.build_empty_column(
            table,
            SQLiteDataType.TEXT,
            name="email",
            is_nullable=True,
            check="email LIKE '%@%'",
        )
        email_column.add()
        table.columns.set_value(list(table.columns.get_value()) + [email_column])

        # Valid email should insert
        valid_record = ctx.build_empty_record(table, values={"name": "Alice", "email": "alice@example.com"})
        assert valid_record.insert() is True

        # Invalid email should fail
        invalid_record = ctx.build_empty_record(table, values={"name": "Bob", "email": "invalidemail"})
        assert invalid_record.insert() is False

        table.drop()

    def test_table_truncate(self, sqlite_session, sqlite_database):
        """Test table truncation."""
        table = create_users_table(sqlite_database, sqlite_session)
        table.load_records()  # Initialize records before build_empty_record

        record = sqlite_session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        assert len(table.records.get_value()) == 1

        assert table.truncate() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()

    def test_index_create_and_drop(self, sqlite_session, sqlite_database):
        """Test index creation and deletion."""
        table = create_users_table(sqlite_database, sqlite_session)

        idx_name = sqlite_session.context.build_empty_index(
            table,
            SQLiteIndexType.INDEX,
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

    def test_view_create_and_drop(self, sqlite_session, sqlite_database):
        """Test view creation and deletion."""
        table = create_users_table(sqlite_database, sqlite_session)

        view = sqlite_session.context.build_empty_view(
            sqlite_database,
            name="active_users_view",
            sql="SELECT * FROM users WHERE name IS NOT NULL",
        )
        assert view.create() is True

        # Refresh views to verify view was created
        sqlite_database.views.refresh()
        views = sqlite_database.views.get_value()
        assert any(v.name == "active_users_view" for v in views)

        assert view.drop() is True

        # Refresh views to verify view was deleted
        sqlite_database.views.refresh()
        views = sqlite_database.views.get_value()
        assert not any(v.name == "active_users_view" for v in views)

        table.drop()

    def test_trigger_create_and_drop(self, sqlite_session, sqlite_database):
        """Test trigger creation and deletion."""
        table = create_users_table(sqlite_database, sqlite_session)

        trigger = sqlite_session.context.build_empty_trigger(
            sqlite_database,
            name="trg_users_insert",
            sql="AFTER INSERT ON users BEGIN SELECT 1; END",
        )
        assert trigger.create() is True

        # Refresh triggers to verify trigger was created
        sqlite_database.triggers.refresh()
        triggers = sqlite_database.triggers.get_value()
        assert any(t.name == "trg_users_insert" for t in triggers)

        assert trigger.drop() is True

        # Refresh triggers to verify trigger was deleted
        sqlite_database.triggers.refresh()
        triggers = sqlite_database.triggers.get_value()
        assert not any(t.name == "trg_users_insert" for t in triggers)

        table.drop()
