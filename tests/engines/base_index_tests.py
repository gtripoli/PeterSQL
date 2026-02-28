import pytest


class BaseIndexTests:
    
    def test_index_create_and_drop(self, session, database, create_users_table, indextype_class):
        table = create_users_table(database, session)

        idx_name = session.context.build_empty_index(
            table,
            indextype_class.INDEX,
            ["name"],
            name="idx_name",
        )
        assert idx_name.create() is True

        table.indexes.refresh()
        indexes = table.indexes.get_value()
        assert any(i.name == "idx_name" for i in indexes)

        assert idx_name.drop() is True

        table.indexes.refresh()
        indexes = table.indexes.get_value()
        assert not any(i.name == "idx_name" for i in indexes)

        table.drop()
