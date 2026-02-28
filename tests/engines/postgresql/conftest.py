import pytest


from testcontainers.postgres import PostgresContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.postgresql.database import PostgreSQLTable
from structures.engines.postgresql.datatype import PostgreSQLDataType
from structures.engines.postgresql.indextype import PostgreSQLIndexType

POSTGRESQL_VERSIONS: list[str] = [
    "postgres:latest",
    "postgres:16",
    "postgres:15",
]


def create_users_table_postgresql(postgresql_database, postgresql_session) -> PostgreSQLTable:
    ctx = postgresql_session.context

    table = ctx.build_empty_table(postgresql_database, name="users")
    table.schema = "public"

    id_column = ctx.build_empty_column(
        table,
        PostgreSQLDataType.SERIAL,
        name="id",
        is_nullable=False,
    )

    name_column = ctx.build_empty_column(
        table,
        PostgreSQLDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        PostgreSQLIndexType.PRIMARY,
        ["id"],
        name="users_pkey",
    )
    table.indexes.append(primary_index)

    table.create()
    postgresql_database.tables.refresh()
    return next(t for t in postgresql_database.tables.get_value() if t.name == "users")


def pytest_generate_tests(metafunc):
    if "postgresql_version" in metafunc.fixturenames:
        metafunc.parametrize("postgresql_version", POSTGRESQL_VERSIONS, scope="module")


@pytest.fixture(scope="module")
def postgresql_container(postgresql_version):
    container = PostgresContainer(
        postgresql_version,
        name=f"petersql_test_{postgresql_version.replace(':', '_')}",
        mem_limit="512m",
        memswap_limit="768m",
        nano_cpus=1_000_000_000,
        shm_size="128m",
    )
    
    with container:
        yield container


@pytest.fixture(scope="module")
def postgresql_session(postgresql_container):
    """Fixture that provides a PostgreSQL session for tests."""
    config = CredentialsConfiguration(
        hostname=postgresql_container.get_container_host_ip(),
        username=postgresql_container.username,
        password=postgresql_container.password,
        port=postgresql_container.get_exposed_port(5432),
    )
    connection = Connection(
        id=1,
        name="test_session",
        engine=ConnectionEngine.POSTGRESQL,
        configuration=config,
    )
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.fixture(scope="function")
def postgresql_database(postgresql_session):
    """Fixture that provides a PostgreSQL database for tests."""
    # PostgreSQL uses the 'test' database created by the container
    # The 'public' schema is the default schema in that database
    postgresql_session.context.databases.refresh()
    database = next(db for db in postgresql_session.context.databases.get_value() if db.name == "test")
    yield database
    # Cleanup: drop all tables in public schema
    database.tables.refresh()
    for table in database.tables.get_value():
        postgresql_session.context.execute(f"DROP TABLE IF EXISTS public.{table.name} CASCADE")


# Unified fixtures for base test suites
@pytest.fixture
def session(postgresql_session):
    """Alias for postgresql_session to match base test suite parameter names."""
    return postgresql_session


@pytest.fixture
def database(postgresql_database):
    """Alias for postgresql_database to match base test suite parameter names."""
    return postgresql_database


@pytest.fixture
def create_users_table():
    """Provide the create_users_table helper function."""
    return create_users_table_postgresql


@pytest.fixture
def datatype_class():
    """Provide the engine-specific datatype class."""
    return PostgreSQLDataType


@pytest.fixture
def indextype_class():
    """Provide the engine-specific indextype class."""
    return PostgreSQLIndexType
