import pytest

from structures.engines.indextype import SQLIndexType, StandardIndexType
from structures.engines.sqlite.indextype import SQLiteIndexType
from structures.engines.mariadb.indextype import MariaDBIndexType
from structures.engines.mysql.indextype import MySQLIndexType


class TestSQLIndexType:
    """Tests for SQLIndexType."""

    def test_index_type_str(self):
        """Test string representation."""
        idx = StandardIndexType.PRIMARY
        assert str(idx) == "PRIMARY"

    def test_index_type_hash(self):
        """Test hash."""
        idx = StandardIndexType.PRIMARY
        assert hash(idx) == hash("PRIMARY")

    def test_index_type_equality(self):
        """Test equality."""
        idx1 = StandardIndexType.PRIMARY
        idx2 = StandardIndexType.PRIMARY
        assert idx1 == idx2

    def test_index_type_inequality(self):
        """Test inequality."""
        idx1 = StandardIndexType.PRIMARY
        idx2 = StandardIndexType.INDEX
        assert idx1 != idx2

    def test_primary_is_primary(self):
        """Test PRIMARY is_primary flag."""
        assert StandardIndexType.PRIMARY.is_primary is True
        assert StandardIndexType.PRIMARY.is_unique is False

    def test_unique_is_unique(self):
        """Test UNIQUE is_unique flag."""
        assert StandardIndexType.UNIQUE.is_unique is True
        assert StandardIndexType.UNIQUE.is_primary is False

    def test_index_flags(self):
        """Test INDEX flags."""
        assert StandardIndexType.INDEX.is_unique is False
        assert StandardIndexType.INDEX.is_primary is False


class TestStandardIndexType:
    """Tests for StandardIndexType.get_all()."""

    def test_get_all(self):
        """Test get_all returns all types."""
        types = StandardIndexType.get_all()
        assert len(types) >= 3
        names = [t.name for t in types]
        assert "PRIMARY" in names
        assert "UNIQUE INDEX" in names
        assert "INDEX" in names


class TestSQLiteIndexType:
    """Tests for SQLiteIndexType."""

    def test_get_all(self):
        """Test SQLite index types."""
        types = SQLiteIndexType.get_all()
        assert len(types) >= 3

    def test_primary(self):
        """Test SQLite PRIMARY."""
        assert SQLiteIndexType.PRIMARY.is_primary is True

    def test_unique(self):
        """Test SQLite UNIQUE."""
        assert SQLiteIndexType.UNIQUE.is_unique is True


class TestMariaDBIndexType:
    """Tests for MariaDBIndexType."""

    def test_get_all(self):
        """Test MariaDB index types."""
        types = MariaDBIndexType.get_all()
        assert len(types) >= 3

    def test_fulltext(self):
        """Test MariaDB FULLTEXT index."""
        assert hasattr(MariaDBIndexType, 'FULLTEXT')


class TestMySQLIndexType:
    """Tests for MySQLIndexType."""

    def test_get_all(self):
        """Test MySQL index types."""
        types = MySQLIndexType.get_all()
        assert len(types) >= 3

    def test_fulltext(self):
        """Test MySQL FULLTEXT index."""
        assert hasattr(MySQLIndexType, 'FULLTEXT')
