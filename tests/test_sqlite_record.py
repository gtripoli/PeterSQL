import pytest
from unittest.mock import Mock, MagicMock, patch

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteRecord, SQLiteColumn
from structures.engines.sqlite.datatype import SQLiteDataType


class TestSQLiteRecord:
    @pytest.fixture
    def database(self, sqlite_session):
        db = SQLiteDatabase(id=1, name='main', context=sqlite_session.context)
        return db

    @pytest.fixture
    def table(self, database):
        table = SQLiteTable(
            id=1,
            name='users',
            database=database,
            engine='sqlite'
        )
        # Add columns to table
        id_col = SQLiteColumn(id=1, name='id', table=table, datatype=SQLiteDataType.INTEGER)
        name_col = SQLiteColumn(id=2, name='name', table=table, datatype=SQLiteDataType.TEXT)
        table.columns._value = [id_col, name_col]
        table.columns._loaded = True
        # Create the table in DB for integration tests
        table.create()
        return table

    def test_record_creation(self, table):
        record = SQLiteRecord(
            id=1,
            table=table,
            values={'name': 'John', 'age': 30}
        )
        assert record.id == 1
        assert record.table.name == table.name  # Check name instead of full equality
        assert record.values == {'name': 'John', 'age': 30}

    def test_record_equality(self, table):
        record1 = SQLiteRecord(id=1, table=table, values={'name': 'John'})
        record2 = SQLiteRecord(id=1, table=table, values={'name': 'John'})
        record3 = SQLiteRecord(id=2, table=table, values={'name': 'Jane'})

        assert record1 == record2
        assert record1 != record3

    def test_record_is_new(self, table):
        new_record = SQLiteRecord(id=-1, table=table, values={})
        existing_record = SQLiteRecord(id=1, table=table, values={})

        assert new_record.is_new() == True
        assert existing_record.is_new() == False

    def test_insert_record(self, table):
        record = SQLiteRecord(
            id=1,
            table=table,
            values={'id': '1', 'name': 'John'}
        )

        mock_transaction = MagicMock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=None)

        with patch.object(table.database.context, 'transaction', return_value=mock_transaction) as mock_trans, \
             patch.object(record, 'raw_insert_record', return_value="INSERT SQL") as mock_raw_insert, \
             patch.object(mock_transaction, 'execute', return_value=True) as mock_execute:
            
            result = record.insert()
            assert result == True
            mock_trans.assert_called_once()
            mock_raw_insert.assert_called_once()
            mock_execute.assert_called_once_with("INSERT SQL")

    def test_update_record(self, table):
        record = SQLiteRecord(
            id=1,
            table=table,
            values={'name': 'Jane'}
        )

        mock_transaction = MagicMock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=None)

        with patch.object(table.database.context, 'transaction', return_value=mock_transaction) as mock_trans, \
             patch.object(record, 'raw_update_record', return_value="UPDATE SQL") as mock_raw_update, \
             patch.object(mock_transaction, 'execute', return_value=True) as mock_execute:
            
            result = record.update()
            assert result == True
            mock_trans.assert_called_once()
            mock_raw_update.assert_called_once()
            mock_execute.assert_called_once_with("UPDATE SQL")

    def test_delete_record(self, table):
        record = SQLiteRecord(
            id=1,
            table=table,
            values={}
        )

        mock_transaction = MagicMock()
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=None)

        with patch.object(table.database.context, 'transaction', return_value=mock_transaction) as mock_trans, \
             patch.object(record, 'raw_delete_record', return_value="DELETE SQL") as mock_raw_delete, \
             patch.object(mock_transaction, 'execute', return_value=True) as mock_execute:
            
            result = record.delete()
            assert result == True
            mock_trans.assert_called_once()
            mock_raw_delete.assert_called_once()
            mock_execute.assert_called_once_with("DELETE SQL")
