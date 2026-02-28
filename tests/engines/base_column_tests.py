import pytest


class BaseColumnTests:
    
    def test_column_add(self, session, database, create_users_table, datatype_class):
        table = create_users_table(database, session)

        email_column = session.context.build_empty_column(
            table,
            datatype_class.VARCHAR,
            name="email",
            is_nullable=True,
            length=255,
        )
        assert email_column.add() is True

        table.columns.refresh()
        columns = table.columns.get_value()
        assert any(c.name == "email" for c in columns)

        table.drop()
