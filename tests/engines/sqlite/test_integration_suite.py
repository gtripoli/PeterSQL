import pytest
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType

from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests


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
@pytest.mark.skip(reason="SQLite requires foreign keys to be defined inline in CREATE TABLE statement")
class TestSQLiteForeignKey(BaseForeignKeyTests):
    
    def get_datatype_class(self):
        return SQLiteDataType

    def get_indextype_class(self):
        return SQLiteIndexType

    def get_primary_key_name(self) -> str:
        return "PRIMARY"


@pytest.mark.integration
class TestSQLiteTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {table_name} BEGIN SELECT 1; END"


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
