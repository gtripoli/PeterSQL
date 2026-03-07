import pytest


class BaseTableTests:
    
    def test_table_create_and_drop(self, session, database, create_users_table):
        table = create_users_table(database, session)
        assert table.is_valid is True
        assert table.id >= 0

        tables = database.tables.get_value()
        assert any(t.name == "users" for t in tables)

        assert table.drop() is True

        database.tables.refresh()
        tables = database.tables.get_value()
        assert not any(t.name == "users" for t in tables)

    def test_table_truncate(self, session, database, create_users_table):
        table = create_users_table(database, session)
        table.load_records()

        record = session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        assert len(table.records.get_value()) == 1

        assert table.truncate() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()

    def test_table_rename(self, session, database, create_users_table):
        table = create_users_table(database, session)
        original_name = table.name

        new_name = "users_renamed"
        table.rename(table, new_name)
        table.name = new_name

        database.tables.refresh()
        tables = database.tables.get_value()
        assert any(t.name == new_name for t in tables)
        assert not any(t.name == original_name for t in tables)

        renamed_table = next(t for t in tables if t.name == new_name)
        renamed_table.drop()
