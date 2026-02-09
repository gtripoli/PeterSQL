import pytest

from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mariadb.datatype import MariaDBDataType


class TestDataTypeProperties:
    """Tests for datatype properties (has_length, has_precision, has_set)."""

    def test_varchar_has_length(self):
        """Test VARCHAR types have length property."""
        assert SQLiteDataType.VARCHAR.has_length is True
        assert MySQLDataType.VARCHAR.has_length is True
        assert MariaDBDataType.VARCHAR.has_length is True

    def test_decimal_has_precision(self):
        """Test DECIMAL types have precision property."""
        assert MySQLDataType.DECIMAL.has_precision is True
        assert MariaDBDataType.DECIMAL.has_precision is True

    def test_enum_has_set(self):
        """Test ENUM types have set property."""
        assert MySQLDataType.ENUM.has_set is True
        assert MariaDBDataType.ENUM.has_set is True

    def test_integer_no_length(self):
        """Test INTEGER types don't have length."""
        assert SQLiteDataType.INTEGER.has_length is False
        assert MySQLDataType.INT.has_length is False


class TestDataTypeGetAll:
    """Tests for get_all method."""

    def test_sqlite_get_all(self):
        """Test SQLite get_all returns all types."""
        all_types = SQLiteDataType.get_all()
        assert len(all_types) > 0
        assert SQLiteDataType.INTEGER in all_types
        assert SQLiteDataType.TEXT in all_types

    def test_mysql_get_all(self):
        """Test MySQL get_all returns all types."""
        all_types = MySQLDataType.get_all()
        assert len(all_types) > 0
        assert MySQLDataType.INT in all_types
        assert MySQLDataType.VARCHAR in all_types

    def test_mariadb_get_all(self):
        """Test MariaDB get_all returns all types."""
        all_types = MariaDBDataType.get_all()
        assert len(all_types) > 0
        assert MariaDBDataType.INT in all_types
