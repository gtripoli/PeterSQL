import pytest

from structures.engines.datatype import DataTypeCategory, SQLDataType
from structures.engines.sqlite.datatype import SQLiteDataType


class TestSQLDataType:
    def test_creation(self):
        dt = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True)
        assert dt.name == "VARCHAR"
        assert dt.category == DataTypeCategory.TEXT
        assert dt.has_length == True
        assert dt.has_precision == False


class TestSQLiteDataType:
    def test_constants(self):
        dt = SQLiteDataType.INTEGER
        assert dt.name == 'INTEGER'
        assert dt.category == DataTypeCategory.INTEGER

        dt2 = SQLiteDataType.TEXT
        assert dt2.name == 'TEXT'
        assert dt2.category == DataTypeCategory.TEXT

        dt3 = SQLiteDataType.REAL
        assert dt3.name == 'REAL'
        assert dt3.category == DataTypeCategory.REAL

        dt4 = SQLiteDataType.BLOB
        assert dt4.name == 'BLOB'
        assert dt4.category == DataTypeCategory.BINARY
