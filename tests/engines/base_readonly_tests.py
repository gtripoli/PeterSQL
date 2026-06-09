import pytest


class BaseReadOnlyTests:
    """Tests verifying that read-only connections block all write operations."""

    def test_read_only_blocks_insert(self, session, database, create_users_table):
        table = create_users_table(database, session)

        session.connection.read_only = True
        try:
            record = session.context.build_empty_record(table, values={"name": "Blocked"})
            with pytest.raises(PermissionError):
                record.insert()
        finally:
            session.connection.read_only = False
            table.drop()

    def test_read_only_blocks_update(self, session, database, create_users_table):
        table = create_users_table(database, session)
        record = session.context.build_empty_record(table, values={"name": "Before"})
        record.insert()
        table.load_records()
        record = table.records.get_value()[0]

        session.connection.read_only = True
        try:
            record.values["name"] = "After"
            with pytest.raises(PermissionError):
                record.update()
        finally:
            session.connection.read_only = False
            table.drop()

    def test_read_only_blocks_delete(self, session, database, create_users_table):
        table = create_users_table(database, session)
        record = session.context.build_empty_record(table, values={"name": "ToDelete"})
        record.insert()
        table.load_records()
        record = table.records.get_value()[0]

        session.connection.read_only = True
        try:
            with pytest.raises(PermissionError):
                record.delete()
        finally:
            session.connection.read_only = False
            table.drop()

    def test_read_only_blocks_create_table(self, session, database):
        session.connection.read_only = True
        try:
            with pytest.raises(PermissionError):
                session.context.execute("CREATE TABLE _ro_test (id INTEGER);")
        finally:
            session.connection.read_only = False

    def test_read_only_blocks_drop_table(self, session, database, create_users_table):
        table = create_users_table(database, session)

        session.connection.read_only = True
        try:
            with pytest.raises(PermissionError):
                session.context.execute(f"DROP TABLE users;")
        finally:
            session.connection.read_only = False
            table.drop()

    def test_read_only_allows_select(self, session, database, create_users_table):
        table = create_users_table(database, session)
        record = session.context.build_empty_record(table, values={"name": "Readable"})
        record.insert()

        session.connection.read_only = True
        try:
            table.load_records()
            records = table.records.get_value()
            assert len(records) == 1
            assert records[0].values["name"] == "Readable"
        finally:
            session.connection.read_only = False
            table.drop()