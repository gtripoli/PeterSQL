import pytest
from structures.engines.mariadb.datatype import MariaDBDataType
from structures.engines.mariadb.indextype import MariaDBIndexType

from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests, BaseViewDefinerTests


@pytest.mark.integration
class TestMariaDBTable(BaseTableTests):
    pass


@pytest.mark.integration
class TestMariaDBRecord(BaseRecordTests):
    pass


@pytest.mark.integration
class TestMariaDBColumn(BaseColumnTests):
    pass


@pytest.mark.integration
class TestMariaDBIndex(BaseIndexTests):
    pass


@pytest.mark.integration
class TestMariaDBForeignKey(BaseForeignKeyTests):
    
    def get_datatype_class(self):
        return MariaDBDataType

    def get_indextype_class(self):
        return MariaDBIndexType

    def get_primary_key_name(self) -> str:
        return "PRIMARY"


@pytest.mark.integration
class TestMariaDBTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {db_name}.{table_name} FOR EACH ROW BEGIN END"


@pytest.mark.integration
class TestMariaDBViewSave(BaseViewSaveTests):
    
    def get_view_statement(self) -> str:
        return "SELECT 1 as id, 'test' as name"

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"

    def get_updated_view_statement(self) -> str:
        return "SELECT 1 as id, 'updated' as name"


@pytest.mark.integration
class TestMariaDBViewIsNew(BaseViewIsNewTests):
    
    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"


@pytest.mark.integration
class TestMariaDBViewDefiner(BaseViewDefinerTests):
    pass
