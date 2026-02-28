import pytest


class BaseRecordTests:
    
    def test_record_insert(self, session, database, create_users_table):
        table = create_users_table(database, session)

        table.load_records()
        assert len(table.records.get_value()) == 0

        record = session.context.build_empty_record(table, values={"name": "John Doe"})
        assert record.insert() is True

        table.load_records()
        records = table.records.get_value()
        assert len(records) == 1
        assert records[0].values["name"] == "John Doe"

        table.drop()

    def test_record_update(self, session, database, create_users_table):
        table = create_users_table(database, session)
        table.load_records()

        record = session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        record = table.records.get_value()[0]
        assert record.is_new is False

        record.values["name"] = "Jane Doe"
        assert record.update() is True

        table.load_records()
        records = table.records.get_value()
        assert records[0].values["name"] == "Jane Doe"

        table.drop()

    def test_record_delete(self, session, database, create_users_table):
        table = create_users_table(database, session)
        table.load_records()

        record = session.context.build_empty_record(table, values={"name": "John Doe"})
        record.insert()

        table.load_records()
        record = table.records.get_value()[0]
        assert record.delete() is True

        table.load_records()
        assert len(table.records.get_value()) == 0

        table.drop()
