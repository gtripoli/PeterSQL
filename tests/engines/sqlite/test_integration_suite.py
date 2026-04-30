import pytest
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType

from tests.engines.base_database_tests import BaseDatabaseUnsupportedTests
from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_check_tests import BaseCheckTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_readonly_tests import BaseReadOnlyTests
from tests.engines.base_view_tests import (
    BaseViewCreateDropTests,
    BaseViewAlterTests,
    BaseViewSaveTests,
    BaseViewIsNewTests,
    BaseViewColumnsTests,
    BaseViewRecordsTests,
    BaseViewCopyTests,
)


@pytest.mark.integration
class TestSQLiteTable(BaseTableTests):
    pass


@pytest.mark.integration
class TestSQLiteRecord(BaseRecordTests):
    pass


@pytest.mark.integration
class TestSQLiteColumn(BaseColumnTests):
    pass


@pytest.mark.integration
class TestSQLiteIndex(BaseIndexTests):
    pass


@pytest.mark.integration
class TestSQLiteForeignKey(BaseForeignKeyTests):

    def get_datatype_class(self):
        return SQLiteDataType

    def get_indextype_class(self):
        return SQLiteIndexType

    def get_primary_key_name(self) -> str:
        return "PRIMARY"

    def test_foreignkey_create_and_drop(self, session, database, create_users_table):
        pytest.skip(
            "SQLite does not support add/drop foreign key constraints after table creation"
        )

    def test_build_empty_foreign_key_with_append_is_persisted_on_create(
        self,
        session,
        database,
        create_users_table,
    ):
        create_users_table(database, session)

        posts_table = session.context.build_empty_table(database, name="posts")
        id_column = session.context.build_empty_column(
            posts_table,
            self.get_datatype_class().INTEGER,
            name="id",
            is_auto_increment=True,
            is_nullable=False,
        )
        user_id_column = session.context.build_empty_column(
            posts_table,
            self.get_datatype_class().INTEGER,
            name="user_id",
            is_nullable=False,
        )

        posts_table.columns.append(id_column)
        posts_table.columns.append(user_id_column)

        primary_index = session.context.build_empty_index(
            posts_table,
            self.get_indextype_class().PRIMARY,
            ["id"],
            name=self.get_primary_key_name(),
        )
        posts_table.indexes.append(primary_index)

        fk = session.context.build_empty_foreign_key(
            posts_table,
            ["user_id"],
            name="fk_posts_users",
        )
        fk.reference_table = "users"
        fk.reference_columns = ["id"]
        fk.on_delete = "CASCADE"
        fk.on_update = "CASCADE"
        posts_table.foreign_keys.append(fk)

        assert posts_table.create() is True

        database.tables.refresh()
        created_posts_table = next(
            table for table in database.tables.get_value() if table.name == "posts"
        )
        created_posts_table.foreign_keys.refresh()

        foreign_keys = created_posts_table.foreign_keys.get_value()
        assert len(foreign_keys) == 1

        created_foreign_key = foreign_keys[0]
        assert created_foreign_key.columns == ["user_id"]
        assert created_foreign_key.reference_table == "users"
        assert created_foreign_key.reference_columns == ["id"]

        created_posts_table.drop()


@pytest.mark.integration
class TestSQLiteCheck(BaseCheckTests):
    pass


@pytest.mark.integration
class TestSQLiteTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {table_name} BEGIN SELECT 1; END"


@pytest.mark.integration
class TestSQLiteViewCreateDrop(BaseViewCreateDropTests):

    def get_simple_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteViewAlter(BaseViewAlterTests):

    def get_simple_view_statement(self) -> str:
        return "SELECT id FROM users"

    def get_updated_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteViewSave(BaseViewSaveTests):

    def get_view_statement(self) -> str:
        return "SELECT id, name FROM users WHERE id > 0"

    def get_simple_view_statement(self) -> str:
        return "SELECT id FROM users"

    def get_updated_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteViewIsNew(BaseViewIsNewTests):

    def get_simple_view_statement(self) -> str:
        return "SELECT * FROM users"


@pytest.mark.integration
class TestSQLiteViewColumns(BaseViewColumnsTests):

    def get_users_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteViewRecords(BaseViewRecordsTests):

    def get_users_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteViewCopy(BaseViewCopyTests):

    def get_simple_view_statement(self) -> str:
        return "SELECT id, name FROM users"


@pytest.mark.integration
class TestSQLiteDatabase(BaseDatabaseUnsupportedTests):
    pass


@pytest.mark.integration
class TestSQLiteReadOnly(BaseReadOnlyTests):
    pass
