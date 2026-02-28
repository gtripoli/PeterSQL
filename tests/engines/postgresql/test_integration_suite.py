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
from tests.engines.base_check_tests import BaseCheckTests
from tests.engines.base_trigger_tests import BaseTriggerTests
from tests.engines.base_function_tests import BaseFunctionTests
from tests.engines.base_view_tests import BaseViewSaveTests, BaseViewIsNewTests


@pytest.mark.integration
class TestPostgreSQLTable(BaseTableTests):
    pass


@pytest.mark.integration
class TestPostgreSQLRecord(BaseRecordTests):
    pass


@pytest.mark.integration
class TestPostgreSQLColumn(BaseColumnTests):
    pass


@pytest.mark.integration
class TestPostgreSQLIndex(BaseIndexTests):
    pass


@pytest.mark.integration
class TestPostgreSQLForeignKey(BaseForeignKeyTests):
    
    def get_datatype_class(self):
        return PostgreSQLDataType

    def get_indextype_class(self):
        return PostgreSQLIndexType

    def get_primary_key_name(self) -> str:
        return "posts_pkey"


@pytest.mark.integration
class TestPostgreSQLCheck(BaseCheckTests):
    pass


@pytest.mark.integration
class TestPostgreSQLTrigger(BaseTriggerTests):
    
    def get_trigger_statement(self, db_name: str, table_name: str) -> str:
        return f"""
            CREATE OR REPLACE FUNCTION trg_users_insert_func() RETURNS TRIGGER AS $$
            BEGIN
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER trg_users_insert
            AFTER INSERT ON public.{table_name}
            FOR EACH ROW EXECUTE FUNCTION trg_users_insert_func();
        """


@pytest.mark.integration
class TestPostgreSQLViewSave(BaseViewSaveTests):
    
    def get_view_statement(self) -> str:
        return "SELECT 1 as id, 'test' as name"

    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"

    def get_updated_view_statement(self) -> str:
        return "SELECT 1 as id, 'updated' as name"


@pytest.mark.integration
class TestPostgreSQLFunction(BaseFunctionTests):
    
    def get_function_statement(self) -> str:
        return "RETURN x + 1;"
    
    def get_function_parameters(self) -> str:
        return "x integer"
    
    def get_function_returns(self) -> str:
        return "integer"


@pytest.mark.integration
class TestPostgreSQLViewIsNew(BaseViewIsNewTests):
    
    def get_simple_view_statement(self) -> str:
        return "SELECT 1 as id"
