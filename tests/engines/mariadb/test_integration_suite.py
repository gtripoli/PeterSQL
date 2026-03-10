import pytest
from structures.engines.mariadb.datatype import MariaDBDataType
from structures.engines.mariadb.indextype import MariaDBIndexType

from tests.engines.base_database_tests import BaseDatabaseCreateAlterTests
from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_check_tests import BaseCheckTests
from tests.engines.base_procedure_tests import BaseProcedureTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests, BaseViewDefinerTests


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBTable(BaseTableTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBRecord(BaseRecordTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBColumn(BaseColumnTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBIndex(BaseIndexTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBForeignKey(BaseForeignKeyTests):
    
    def get_datatype_class(self):
        return MariaDBDataType

    def get_indextype_class(self):
        return MariaDBIndexType

    def get_primary_key_name(self) -> str:
        return "PRIMARY"


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBCheck(BaseCheckTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBProcedure(BaseProcedureTests):

    def get_procedure_statement(self) -> str:
        return "SELECT 1"

    def get_updated_procedure_statement(self) -> str:
        return "SELECT 2"


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {db_name}.{table_name} FOR EACH ROW BEGIN END"


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBViewSave(BaseViewSaveTests):
    
    def get_view_statement(self) -> str:
        return "SELECT 1 as id, 'test' as name"

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"

    def get_updated_view_statement(self) -> str:
        return "SELECT 1 as id, 'updated' as name"


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBViewIsNew(BaseViewIsNewTests):
    
    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBViewDefiner(BaseViewDefinerTests):
    pass


@pytest.mark.integration
@pytest.mark.xdist_group("mariadb")
class TestMariaDBDatabase(BaseDatabaseCreateAlterTests):

    def get_create_options(self) -> dict[str, str]:
        return {
            "character_set": "utf8mb4",
            "default_collation": "utf8mb4_general_ci",
        }

    def get_alter_options(self) -> dict[str, str]:
        return {
            "character_set": "utf8mb4",
            "default_collation": "utf8mb4_general_ci",
        }
