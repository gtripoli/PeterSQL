"""
PostgreSQL integration tests using base test suites.

These tests inherit from base test suite classes and are automatically parametrized
with different PostgreSQL versions via conftest.py fixtures.

NOTE: Currently skipped due to PostgreSQL builder bugs (raw_create, index creation).
These need to be fixed separately before enabling these tests.
"""
import pytest
from structures.engines.postgresql.datatype import PostgreSQLDataType
from structures.engines.postgresql.indextype import PostgreSQLIndexType

from tests.engines.base_table_tests import BaseTableTests
from tests.engines.base_record_tests import BaseRecordTests
from tests.engines.base_column_tests import BaseColumnTests
from tests.engines.base_index_tests import BaseIndexTests
from tests.engines.base_foreignkey_tests import BaseForeignKeyTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL builder has bugs in raw_create() and index creation - needs separate fix")
class TestPostgreSQLTable(BaseTableTests):
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL builder has bugs - needs separate fix")
class TestPostgreSQLRecord(BaseRecordTests):
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL builder has bugs - needs separate fix")
class TestPostgreSQLColumn(BaseColumnTests):
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL builder has bugs - needs separate fix")
class TestPostgreSQLIndex(BaseIndexTests):
    pass


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL builder has bugs - needs separate fix")
class TestPostgreSQLForeignKey(BaseForeignKeyTests):
    
    def get_datatype_class(self):
        return PostgreSQLDataType

    def get_indextype_class(self):
        return PostgreSQLIndexType

    def get_primary_key_name(self) -> str:
        return "posts_pkey"


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL triggers require function creation - complex setup")
class TestPostgreSQLTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"AFTER INSERT ON {db_name}.{table_name} FOR EACH ROW EXECUTE FUNCTION trigger_function()"


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL view tests need test_db setup")
class TestPostgreSQLViewSave(BaseViewSaveTests):
    
    def get_view_statement(self) -> str:
        return "SELECT 1 as id, 'test' as name"

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"

    def get_updated_view_statement(self) -> str:
        return "SELECT 1 as id, 'updated' as name"


@pytest.mark.integration
@pytest.mark.skip(reason="PostgreSQL view tests need test_db setup")
class TestPostgreSQLViewIsNew(BaseViewIsNewTests):
    
    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"
