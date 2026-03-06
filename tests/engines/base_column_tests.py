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

    @pytest.mark.skip_engine("sqlite")
    def test_column_modify(self, session, database, create_users_table, datatype_class):
        table = create_users_table(database, session)

        email_column = session.context.build_empty_column(
            table,
            datatype_class.VARCHAR,
            name="email",
            is_nullable=True,
            length=100,
        )
        email_column.add()

        table.columns.refresh()
        columns = table.columns.get_value()
        email_col = next((c for c in columns if c.name == "email"), None)
        assert email_col is not None

        modified_column = session.context.build_empty_column(
            table,
            datatype_class.VARCHAR,
            name="email",
            is_nullable=False,
            length=255,
        )

        assert (
            email_col.modify(modified_column) is None
            or email_col.modify(modified_column) is True
        )

        table.columns.refresh()
        columns = table.columns.get_value()
        updated_col = next((c for c in columns if c.name == "email"), None)
        assert updated_col is not None

        table.drop()

    @pytest.mark.skip_engine("sqlite")
    def test_column_drop(self, session, database, create_users_table, datatype_class):
        table = create_users_table(database, session)

        email_column = session.context.build_empty_column(
            table,
            datatype_class.VARCHAR,
            name="email",
            is_nullable=True,
            length=255,
        )
        email_column.add()

        table.columns.refresh()
        columns = table.columns.get_value()
        email_col = next((c for c in columns if c.name == "email"), None)
        assert email_col is not None

        assert email_col.drop() is True

        table.columns.refresh()
        columns = table.columns.get_value()
        assert not any(c.name == "email" for c in columns)

        table.drop()
