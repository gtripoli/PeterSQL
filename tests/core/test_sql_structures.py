import pytest

from structures.engines.sqlite.database import (
    SQLiteDatabase, SQLiteTable, SQLiteColumn, SQLiteIndex, SQLiteForeignKey
)
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


class TestSQLiteColumn:
    """Tests for SQLiteColumn."""

    @pytest.fixture
    def table(self, sqlite_session):
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        return SQLiteTable(id=1, name="test_table", database=database)

    def test_column_creation(self, table):
        """Test column creation."""
        column = SQLiteColumn(
            id=1,
            name="test_col",
            table=table,
            datatype=SQLiteDataType.TEXT,
        )
        assert column.name == "test_col"
        assert column.datatype == SQLiteDataType.TEXT

    def test_column_nullable(self, table):
        """Test nullable column."""
        column = SQLiteColumn(
            id=1,
            name="nullable_col",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=True,
        )
        assert column.is_nullable is True

    def test_column_not_nullable(self, table):
        """Test not nullable column."""
        column = SQLiteColumn(
            id=1,
            name="required_col",
            table=table,
            datatype=SQLiteDataType.TEXT,
            is_nullable=False,
        )
        assert column.is_nullable is False

    def test_column_with_default(self, table):
        """Test column with default value."""
        column = SQLiteColumn(
            id=1,
            name="default_col",
            table=table,
            datatype=SQLiteDataType.TEXT,
            server_default="'default_value'",
        )
        assert column.server_default == "'default_value'"

    def test_column_auto_increment(self, table):
        """Test auto increment column."""
        column = SQLiteColumn(
            id=1,
            name="id",
            table=table,
            datatype=SQLiteDataType.INTEGER,
            is_auto_increment=True,
        )
        assert column.is_auto_increment is True

    def test_column_with_length(self, table):
        """Test column with length."""
        column = SQLiteColumn(
            id=1,
            name="varchar_col",
            table=table,
            datatype=SQLiteDataType.VARCHAR,
            length=255,
        )
        assert column.length == 255


class TestSQLiteIndex:
    """Tests for SQLiteIndex."""

    @pytest.fixture
    def table(self, sqlite_session):
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        return SQLiteTable(id=1, name="test_table", database=database)

    def test_index_creation(self, table):
        """Test index creation."""
        index = SQLiteIndex(
            id=1,
            name="idx_test",
            type=SQLiteIndexType.INDEX,
            columns=["col1", "col2"],
            table=table,
        )
        assert index.name == "idx_test"
        assert index.columns == ["col1", "col2"]

    def test_primary_key_index(self, table):
        """Test primary key index."""
        index = SQLiteIndex(
            id=1,
            name="PRIMARY",
            type=SQLiteIndexType.PRIMARY,
            columns=["id"],
            table=table,
        )
        assert index.type == SQLiteIndexType.PRIMARY

    def test_unique_index(self, table):
        """Test unique index."""
        index = SQLiteIndex(
            id=1,
            name="idx_unique",
            type=SQLiteIndexType.UNIQUE,
            columns=["email"],
            table=table,
        )
        assert index.type == SQLiteIndexType.UNIQUE


class TestSQLiteForeignKey:
    """Tests for SQLiteForeignKey."""

    @pytest.fixture
    def table(self, sqlite_session):
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        return SQLiteTable(id=1, name="orders", database=database)

    def test_foreign_key_creation(self, table):
        """Test foreign key creation."""
        fk = SQLiteForeignKey(
            id=1,
            name="fk_user",
            table=table,
            columns=["user_id"],
            reference_table="users",
            reference_columns=["id"],
        )
        assert fk.columns == ["user_id"]
        assert fk.reference_table == "users"
        assert fk.reference_columns == ["id"]

    def test_foreign_key_on_delete(self, table):
        """Test foreign key with ON DELETE."""
        fk = SQLiteForeignKey(
            id=1,
            name="fk_cascade",
            table=table,
            columns=["parent_id"],
            reference_table="parents",
            reference_columns=["id"],
            on_delete="CASCADE",
        )
        assert fk.on_delete == "CASCADE"

    def test_foreign_key_on_update(self, table):
        """Test foreign key with ON UPDATE."""
        fk = SQLiteForeignKey(
            id=1,
            name="fk_update",
            table=table,
            columns=["ref_id"],
            reference_table="refs",
            reference_columns=["id"],
            on_update="SET NULL",
        )
        assert fk.on_update == "SET NULL"


class TestSQLiteTable:
    """Tests for SQLiteTable."""

    def test_table_creation(self, sqlite_session):
        """Test table creation."""
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        table = SQLiteTable(id=1, name="test_table", database=database)

        assert table.name == "test_table"
        assert table.database == database

    def test_table_with_comment(self, sqlite_session):
        """Test table with comment."""
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        table = SQLiteTable(
            id=1,
            name="commented_table",
            database=database,
            comment="This is a test table",
        )
        assert table.comment == "This is a test table"


class TestSQLiteDatabase:
    """Tests for SQLiteDatabase."""

    def test_database_creation(self, sqlite_session):
        """Test database creation."""
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        assert database.name == "main"

    def test_database_sql_safe_name(self, sqlite_session):
        """Test sql_safe_name property."""
        database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
        assert database.sql_safe_name == "main"

    def test_database_with_special_name(self, sqlite_session):
        """Test database with special name."""
        database = SQLiteDatabase(id=1, name="my database", context=sqlite_session.context)
        quote = sqlite_session.context.IDENTIFIER_QUOTE
        assert database.sql_safe_name == f'{quote}my database{quote}'
