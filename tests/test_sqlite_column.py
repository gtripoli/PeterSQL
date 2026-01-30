import pytest
from unittest.mock import Mock, patch

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteColumn
from structures.engines.sqlite.datatype import SQLiteDataType


class TestSQLiteColumn:
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
        id_col = SQLiteColumn(id=1, name='id', table=table, datatype=SQLiteDataType.INTEGER)
        name_col = SQLiteColumn(id=2, name='name', table=table, datatype=SQLiteDataType.TEXT)
        table.columns._value = [id_col, name_col]
        table.columns._loaded = True
        table.create()
        return table

    def test_column_creation(self, table):
        datatype = SQLiteDataType.INTEGER
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=datatype
        )
        assert column.id == 1
        assert column.name == 'id'
        assert column.datatype == datatype
        assert column.table.name == table.name  # Check name instead of full equality



    def test_column_properties(self, table):
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER,
            is_auto_increment=True,
            is_nullable=False
        )
        assert column.is_auto_increment == True
        assert column.is_nullable == False
        assert column.default == 'AUTO_INCREMENT'

    def test_column_validity(self, table):
        # Valid column
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )
        assert column.is_valid == True

        # Invalid: no name
        invalid_column = SQLiteColumn(
            id=2,
            name='',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )
        assert invalid_column.is_valid == False

    @patch('structures.engines.sqlite.database.SQLiteColumnBuilder')
    def test_add_column(self, mock_builder, table):
        mock_builder.return_value = Mock()
        mock_builder.return_value.__str__ = Mock(return_value='id INTEGER PRIMARY KEY')

        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = column.add()
            assert result == True
            mock_execute.assert_called_once()
            args, kwargs = mock_execute.call_args
            assert 'ALTER TABLE `users` ADD COLUMN' in args[0]

    @patch('structures.engines.sqlite.database.SQLiteColumnBuilder')
    def test_rename_column(self, mock_builder, table):
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = column.rename('new_id')
            assert result == True
            mock_execute.assert_called_once_with("ALTER TABLE `users` RENAME COLUMN `id` TO `new_id`")

    @patch('structures.engines.sqlite.database.SQLiteColumnBuilder')
    def test_drop_column(self, mock_builder, table):
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = column.drop(table, column)
            assert result == True
            mock_execute.assert_called_once_with("ALTER TABLE `users` DROP COLUMN `id`")

    def test_modify_column(self, table):
        # This method is complex, involving renaming and recreating table
        # For testing, we can mock the parts
        column = SQLiteColumn(
            id=1,
            name='id',
            table=table,
            datatype=SQLiteDataType.INTEGER
        )

        # Mock the table methods
        with patch.object(table, 'rename', return_value=True) as mock_rename, \
             patch.object(table, 'create', return_value=True) as mock_create, \
             patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            
            # Set up table.columns to include the column
            table.columns = [column]
            
            result = column.modify()
            # Since modify recreates the table, it should return None or something
            # But the method doesn't return anything, so assert no exception
            assert result is None
