import pytest

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


def create_users_table_sqlite(sqlite_database, sqlite_session) -> SQLiteTable:
    ctx = sqlite_session.context

    table = ctx.build_empty_table(sqlite_database, name="users")

    id_column = ctx.build_empty_column(
        table,
        SQLiteDataType.INTEGER,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
    )

    name_column = ctx.build_empty_column(
        table,
        SQLiteDataType.TEXT,
        name="name",
        is_nullable=False,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        SQLiteIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    table.create()
    sqlite_database.tables.refresh()
    return next(t for t in sqlite_database.tables.get_value() if t.name == "users")


@pytest.fixture(scope="module")
def sqlite_session():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=1,
        name="test_session",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.fixture(scope="module")
def sqlite_database(sqlite_session):
    # Use the database from context which has proper handlers configured
    databases = sqlite_session.context.get_databases()
    yield databases[0]


# Unified fixtures for base test suites
@pytest.fixture
def session(sqlite_session):
    """Alias for sqlite_session to match base test suite parameter names."""
    return sqlite_session


@pytest.fixture
def database(sqlite_database):
    """Alias for sqlite_database to match base test suite parameter names."""
    return sqlite_database


@pytest.fixture
def create_users_table():
    """Provide the create_users_table helper function."""
    return create_users_table_sqlite


@pytest.fixture
def datatype_class():
    """Provide the engine-specific datatype class."""
    return SQLiteDataType


@pytest.fixture
def indextype_class():
    """Provide the engine-specific indextype class."""
    return SQLiteIndexType
