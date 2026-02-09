import pytest

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


class TestSQLiteIntegration:
    def test_full_database_workflow(self, sqlite_session, sqlite_database):
        table = SQLiteTable(
            id=1,
            name="users",
            database=sqlite_database,
            engine="sqlite",
        )

        id_column = SQLiteColumn(
            id=1,
            name="id",
            table=table,
            datatype=SQLiteDataType.INTEGER,
            is_auto_increment=True,
            is_nullable=False,
        )

        name_column = SQLiteColumn(
            id=2,
            name="name",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=False,
            length=255,
        )

        table.columns._value = [id_column, name_column]
        table.columns._loaded = True

        primary_index = SQLiteIndex(
            id=1,
            name="PRIMARY",
            type=SQLiteIndexType.PRIMARY,
            columns=["id"],
            table=table,
        )
        table.indexes._value = [primary_index]
        table.indexes._loaded = True

        sqlite_database.tables._value = [table]
        sqlite_database.tables._loaded = True

        table.get_records_handler = (
            lambda t, f=None, l=1000, o=0, ord=None: sqlite_session.context.get_records(
                t,
                filters=f,
                limit=l,
                offset=o,
                orders=ord,
            )
        )

        assert table.is_valid is True

        result = table.create()
        assert result is True

        assert len(sqlite_database.tables.get_value()) == 1
        assert sqlite_database.tables.get_value()[0].name == "users"

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        row = sqlite_session.context.fetchone()
        assert row["name"] == "users"

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0

        new_record = SQLiteRecord(
            id=-1,
            table=table,
            values={"name": "John Doe"},
        )
        result = new_record.insert()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "John Doe"

        record = records[0]
        assert record.is_valid() is True
        assert record.is_new() is False

        record.values["name"] = "Jane Doe"
        result = record.update()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "Jane Doe"

        result = record.delete()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0

        email_column = SQLiteColumn(
            id=3,
            name="email",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=True,
            check="email LIKE '%@%'",
        )

        result = email_column.add()
        assert result is True

        table.columns._value.append(email_column)

        new_record2 = SQLiteRecord(
            id=-1,
            table=table,
            values={"name": "Alice", "email": "alice@example.com"},
        )
        result = new_record2.insert()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "Alice"
        assert records[0].values["email"] == "alice@example.com"

        new_record3 = SQLiteRecord(
            id=-1,
            table=table,
            values={"name": "Bob", "email": "invalidemail"},
        )
        result = new_record3.insert()
        assert result is False

        result = table.truncate()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 0

        new_record4 = SQLiteRecord(
            id=-1,
            table=table,
            values={"name": "Charlie", "email": "charlie@test.com"},
        )
        result = new_record4.insert()
        assert result is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "Charlie"
        assert records[0].values["id"] == 1

        # === INDEX CREATE/DROP ===
        idx_name = SQLiteIndex(
            id=2,
            name="idx_name",
            type=SQLiteIndexType.INDEX,
            columns=["name"],
            table=table,
        )
        assert idx_name.create() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_name'")
        assert sqlite_session.context.fetchone() is not None

        assert idx_name.drop() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_name'")
        assert sqlite_session.context.fetchone() is None

        # === VIEW ===
        view = SQLiteView(
            id=1,
            name="active_users_view",
            database=sqlite_database,
            sql="SELECT * FROM users WHERE name IS NOT NULL",
        )
        assert view.create() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='active_users_view'")
        assert sqlite_session.context.fetchone() is not None

        assert view.drop() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='active_users_view'")
        assert sqlite_session.context.fetchone() is None

        # === TRIGGER ===
        trigger = SQLiteTrigger(
            id=1,
            name="trg_users_insert",
            database=sqlite_database,
            sql="AFTER INSERT ON users BEGIN SELECT 1; END",
            timing="AFTER",
            event="INSERT",
        )
        assert trigger.create() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='trg_users_insert'")
        assert sqlite_session.context.fetchone() is not None

        assert trigger.drop() is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='trg_users_insert'")
        assert sqlite_session.context.fetchone() is None

        # === CLEANUP ===
        result = table.drop()
        assert result is True

        sqlite_session.context.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        row = sqlite_session.context.fetchone()
        assert row is None
