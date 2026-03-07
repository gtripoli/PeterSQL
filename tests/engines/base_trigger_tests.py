import pytest


class BaseTriggerTests:
    
    def test_trigger_create_and_drop(self, session, database, create_users_table):
        table = create_users_table(database, session)

        trigger = session.context.build_empty_trigger(
            database,
            name="trg_users_insert",
            statement=self.get_trigger_statement(database.name, table.name),
        )
        assert trigger.create() is True

        database.triggers.refresh()
        triggers = database.triggers.get_value()
        assert any(t.name == "trg_users_insert" for t in triggers)

        assert trigger.drop() is True

        database.triggers.refresh()
        triggers = database.triggers.get_value()
        assert not any(t.name == "trg_users_insert" for t in triggers)

        table.drop()

    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        raise NotImplementedError("Subclasses must implement get_trigger_statement()")
