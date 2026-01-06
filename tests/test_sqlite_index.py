import pytest
import tempfile
import os
from unittest.mock import patch

from structures.session import Session
from structures.engines import SessionEngine
from structures.configurations import SourceConfiguration
from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteIndex, SQLiteColumn
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


class TestSQLiteIndex:
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

    def test_index_creation(self, table):
        index = SQLiteIndex(
            id=1,
            name='idx_users_id',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )
        assert index.id == 1
        assert index.name == 'idx_users_id'
        assert index.type == SQLiteIndexType.PRIMARY
        assert index.columns == ['id']
        assert index.table.name == table.name  # Check name instead of full equality

    def test_index_validity(self, table):
        # Valid index
        index = SQLiteIndex(
            id=1,
            name='idx_users_id',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )
        assert index.is_valid == True

        # Invalid: no name
        invalid_index = SQLiteIndex(
            id=2,
            name='',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )
        assert invalid_index.is_valid == False

        # Invalid: no columns
        invalid_index2 = SQLiteIndex(
            id=3,
            name='idx_empty',
            type=SQLiteIndexType.PRIMARY,
            columns=[],
            table=table
        )
        assert invalid_index2.is_valid == False

    def test_create_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='idx_users_id',
            type=SQLiteIndexType.INDEX,
            columns=['id'],
            table=table
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = index.create()
            assert result == True
            mock_execute.assert_called_once_with("CREATE INDEX IF NOT EXISTS idx_users_id ON users(id) ")

    def test_create_unique_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='idx_users_email',
            type=SQLiteIndexType.UNIQUE,
            columns=['email'],
            table=table
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = index.create()
            assert result == True
            mock_execute.assert_called_once_with("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) ")

    def test_create_primary_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='pk_users',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )

        result = index.create()
        assert result == False  # PRIMARY is handled in table creation, so returns False

    def test_drop_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='idx_users_id',
            type=SQLiteIndexType.INDEX,
            columns=['id'],
            table=table
        )

        with patch.object(table.database.context, 'execute', return_value=True) as mock_execute:
            result = index.drop()
            assert result == True
            mock_execute.assert_called_once_with("DROP INDEX IF EXISTS idx_users_id")

    def test_drop_primary_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='pk_users',
            type=SQLiteIndexType.PRIMARY,
            columns=['id'],
            table=table
        )

        result = index.drop()
        assert result == False  # PRIMARY can't be dropped separately

    def test_modify_index(self, table):
        index = SQLiteIndex(
            id=1,
            name='idx_users_id',
            type=SQLiteIndexType.INDEX,
            columns=['id'],
            table=table
        )

        new_index = SQLiteIndex(
            id=1,
            name='idx_users_new',
            type=SQLiteIndexType.UNIQUE,
            columns=['email'],
            table=table
        )

        with patch.object(index, 'drop', return_value=True) as mock_drop, \
             patch.object(new_index, 'create', return_value=True) as mock_create:
            
            index.modify(new_index)
            mock_drop.assert_called_once()
            mock_create.assert_called_once()
