import pytest

from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mariadb.database import MariaDBTable
from structures.engines.mariadb.datatype import MariaDBDataType
from structures.engines.mariadb.indextype import MariaDBIndexType

MARIADB_VERSIONS: list[str] = [
    "mariadb:12",
    "mariadb:11",
    "mariadb:10",
    "mariadb:5",
]


def create_users_table_mariadb(mariadb_database, mariadb_session) -> MariaDBTable:
    ctx = mariadb_session.context
    ctx.set_database(mariadb_database)

    table = ctx.build_empty_table(mariadb_database, name="users", engine="InnoDB", collation_name="utf8mb4_general_ci")

    id_column = ctx.build_empty_column(
        table,
        MariaDBDataType.INT,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
        length=11,
    )

    name_column = ctx.build_empty_column(
        table,
        MariaDBDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        MariaDBIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    table.create()
    mariadb_database.tables.refresh()
    return next(t for t in mariadb_database.tables.get_value() if t.name == "users")


def pytest_generate_tests(metafunc):
    if "mariadb_version" in metafunc.fixturenames:
        metafunc.parametrize("mariadb_version", MARIADB_VERSIONS, scope="module")


@pytest.fixture(scope="module")
def mariadb_container(mariadb_version, worker_id):
    container = MySqlContainer(
        mariadb_version,
        name=f"petersql_test_{worker_id}_{mariadb_version.replace(':', '_')}",
        mem_limit="768m",
        memswap_limit="1g",
        nano_cpus=1_000_000_000,
        shm_size="256m",
    )

    with container:
        yield container


@pytest.fixture(scope="module")
def mariadb_session(mariadb_container):
    config = CredentialsConfiguration(
        hostname=mariadb_container.get_container_host_ip(),
        username="root",
        password=mariadb_container.root_password,
        port=mariadb_container.get_exposed_port(3306),
    )
    connection = Connection(
        id=1,
        name="test_session",
        engine=ConnectionEngine.MARIADB,
        configuration=config,
    )
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.fixture(scope="function")
def mariadb_database(mariadb_session):
    mariadb_session.context.execute("CREATE DATABASE IF NOT EXISTS testdb")
    mariadb_session.context.databases.refresh()
    database = next(db for db in mariadb_session.context.databases.get_value() if db.name == "testdb")
    yield database
    # Cleanup: drop all tables in testdb
    mariadb_session.context.execute("USE testdb")
    mariadb_session.context.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in database.tables.get_value():
        mariadb_session.context.execute(f"DROP TABLE IF EXISTS `testdb`.`{table.name}`")
    mariadb_session.context.execute("SET FOREIGN_KEY_CHECKS = 1")


# Unified fixtures for base test suites
@pytest.fixture
def session(mariadb_session):
    """Alias for mariadb_session to match base test suite parameter names."""
    return mariadb_session


@pytest.fixture
def database(mariadb_database):
    """Alias for mariadb_database to match base test suite parameter names."""
    return mariadb_database


@pytest.fixture
def create_users_table():
    """Provide the create_users_table helper function."""
    return create_users_table_mariadb


@pytest.fixture
def datatype_class():
    """Provide the engine-specific datatype class."""
    return MariaDBDataType


@pytest.fixture
def indextype_class():
    """Provide the engine-specific indextype class."""
    return MariaDBIndexType
