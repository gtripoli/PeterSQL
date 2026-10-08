import pytest

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteColumn
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.builder import SQLiteColumnBuilder
from structures.engines.mariadb.builder import MariaDBColumnBuilder
from structures.engines.mysql.builder import MySQLColumnBuilder


class TestSQLiteColumnBuilder:
    """Tests for SQLiteColumnBuilder."""

    @pytest.fixture
    def table(self, sqlite_session):
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        return SQLiteTable(id=1, name="test_table", database=database)

    def test_builder_simple_column(self, table):
        """Test building simple column."""
        column = SQLiteColumn(
            id=1,
            name="name",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=True,
        )
        builder = SQLiteColumnBuilder(column)
        result = str(builder)

        assert "name" in result
        assert "TEXT" in result
        assert "NULL" in result

    def test_builder_not_null(self, table):
        """Test building NOT NULL column."""
        column = SQLiteColumn(
            id=1,
            name="required",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=False,
        )
        builder = SQLiteColumnBuilder(column)
        result = str(builder)

        assert "NOT NULL" in result

    def test_builder_with_default(self, table):
        """Test building column with default."""
        column = SQLiteColumn(
            id=1,
            name="status",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=True,
            server_default="'active'",
        )
        builder = SQLiteColumnBuilder(column)
        result = str(builder)

        assert "DEFAULT 'active'" in result

    def test_builder_integer_primary_key(self, table):
        """Test building INTEGER PRIMARY KEY column."""
        column = SQLiteColumn(
            id=1,
            name="id",
            table=table,
            datatype=SQLiteDataType.INTEGER,
            is_nullable=False,
            is_auto_increment=True,
        )
        builder = SQLiteColumnBuilder(column)
        result = str(builder)

        assert "INTEGER" in result
        assert "PRIMARY KEY" in result

    def test_builder_varchar_with_length(self, table):
        """Test building VARCHAR with length."""
        column = SQLiteColumn(
            id=1,
            name="email",
            table=table,
            datatype=SQLiteDataType.VARCHAR,
            length=255,
            is_nullable=True,
        )
        builder = SQLiteColumnBuilder(column)
        result = str(builder)

        assert "VARCHAR(255)" in result

    def test_builder_datatype_property(self, table):
        """Test datatype property."""
        column = SQLiteColumn(
            id=1,
            name="amount",
            table=table,
            datatype=SQLiteDataType.REAL,
            is_nullable=True,
        )
        builder = SQLiteColumnBuilder(column)

        assert builder.datatype == "REAL"

    def test_builder_nullable_property(self, table):
        """Test nullable property."""
        column_nullable = SQLiteColumn(
            id=1, name="opt", table=table, datatype=SQLiteDataType.TEXT, is_nullable=True
        )
        column_required = SQLiteColumn(
            id=2, name="req", table=table, datatype=SQLiteDataType.TEXT, is_nullable=False
        )

        assert SQLiteColumnBuilder(column_nullable).nullable == "NULL"
        assert SQLiteColumnBuilder(column_required).nullable == "NOT NULL"


class TestMariaDBFormatSetValues:
    """Tests for MariaDBColumnBuilder._format_set_values."""

    def test_simple_list(self):
        """A plain list of strings is quoted and joined."""
        result = MariaDBColumnBuilder._format_set_values(None, ['EN', 'FR'])
        assert result == "'EN', 'FR'"

    def test_single_quote_escaping(self):
        """Single quotes inside values are escaped as ''."""
        result = MariaDBColumnBuilder._format_set_values(None, ["O'Reilly", 'EN'])
        assert result == "'O''Reilly', 'EN'"

    def test_preformatted_string_passthrough(self):
        """A pre-formatted string (non-list) is returned unchanged."""
        preformatted = "'A', 'B'"
        result = MariaDBColumnBuilder._format_set_values(None, preformatted)
        assert result == preformatted

    def test_non_string_elements_stringified(self):
        """Non-string list elements are stringified and quoted without raising AttributeError."""
        result = MariaDBColumnBuilder._format_set_values(None, [1, 2, 3])
        assert result == "'1', '2', '3'"


class TestMySQLFormatSetValues:
    """Tests for MySQLColumnBuilder._format_set_values."""

    def test_simple_list(self):
        """A plain list of strings is quoted and joined."""
        result = MySQLColumnBuilder._format_set_values(None, ['EN', 'FR'])
        assert result == "'EN', 'FR'"

    def test_single_quote_escaping(self):
        """Single quotes inside values are escaped as ''."""
        result = MySQLColumnBuilder._format_set_values(None, ['EN', "O'Reilly"])
        assert result == "'EN', 'O''Reilly'"

    def test_preformatted_string_passthrough(self):
        """A pre-formatted string (non-list) is returned unchanged."""
        preformatted = "'X', 'Y'"
        result = MySQLColumnBuilder._format_set_values(None, preformatted)
        assert result == preformatted

    def test_non_string_elements_stringified(self):
        """Non-string list elements are stringified and quoted without raising AttributeError."""
        result = MySQLColumnBuilder._format_set_values(None, [True, 42])
        assert result == "'True', '42'"
