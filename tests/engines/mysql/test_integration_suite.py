import pytest
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mysql.indextype import MySQLIndexType

from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_check_tests import BaseCheckTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests, BaseViewDefinerTests


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLTable(BaseTableTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLRecord(BaseRecordTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLColumn(BaseColumnTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLIndex(BaseIndexTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLForeignKey(BaseForeignKeyTests):

    def get_datatype_class(self):
        return MySQLDataType

    def get_indextype_class(self):
        return MySQLIndexType

    def get_primary_key_name(self) -> str:
        return "PRIMARY"


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLCheck(BaseCheckTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLTrigger(BaseTriggerTests):

    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {db_name}.{table_name} FOR EACH ROW BEGIN END"


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLViewSave(BaseViewSaveTests):

    def get_view_statement(self) -> str:
        return "SELECT 1 as id, 'test' as name"

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"

    def get_updated_view_statement(self) -> str:
        return "SELECT 1 as id, 'updated' as name"


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLViewIsNew(BaseViewIsNewTests):

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"


@pytest.mark.integration
@pytest.mark.xdist_group("mysql")
class TestMySQLViewDefiner(BaseViewDefinerTests):
    pass
