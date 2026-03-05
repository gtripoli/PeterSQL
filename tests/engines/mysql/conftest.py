import pytest


from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration
from structures.engines.mysql.database import MySQLTable
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mysql.indextype import MySQLIndexType


MYSQL_VERSIONS: list[str] = [
    "mysql:9",
    "mysql:8",
    # "mysql:5.7",  # Disabled: too slow and resource-intensive
]


def create_users_table_mysql(mysql_database, mysql_session) -> MySQLTable:
    ctx = mysql_session.context
    ctx.set_database(mysql_database)

    table = ctx.build_empty_table(mysql_database, name="users", engine="InnoDB", collation_name="utf8mb4_general_ci")

    id_column = ctx.build_empty_column(
        table,
        MySQLDataType.INT,
        name="id",
        is_auto_increment=True,
        is_nullable=False,
        length=11,
    )

    name_column = ctx.build_empty_column(
        table,
        MySQLDataType.VARCHAR,
        name="name",
        is_nullable=False,
        length=255,
    )

    table.columns.append(id_column)
    table.columns.append(name_column)

    primary_index = ctx.build_empty_index(
        table,
        MySQLIndexType.PRIMARY,
        ["id"],
        name="PRIMARY",
    )
    table.indexes.append(primary_index)

    table.create()
    mysql_database.tables.refresh()
    return next(t for t in mysql_database.tables.get_value() if t.name == "users")


def pytest_generate_tests(metafunc):
    if "mysql_version" in metafunc.fixturenames:
        metafunc.parametrize("mysql_version", MYSQL_VERSIONS, scope="module")


@pytest.fixture(scope="module")
def mysql_container(mysql_version, worker_id):
    container = MySqlContainer(mysql_version, name=f"petersql_test_{worker_id}_{mysql_version.replace(':', '_')}",
                        mem_limit="768m",
                        memswap_limit="1g",
                        nano_cpus=1_000_000_000,
                        shm_size="256m",
                        )
    
    with container:
        yield container


@pytest.fixture(scope="module")
def mysql_session(mysql_container):
    config = CredentialsConfiguration(
        hostname=mysql_container.get_container_host_ip(),
        username="root",
        password=mysql_container.root_password,
        port=mysql_container.get_exposed_port(3306),
    )
    connection = Connection(
        id=1,
        name="test_session",
        engine=ConnectionEngine.MYSQL,
        configuration=config,
    )
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.fixture(scope="function")
def mysql_database(mysql_session):
    mysql_session.context.execute("CREATE DATABASE IF NOT EXISTS testdb")
    mysql_session.context.databases.refresh()
    database = next(db for db in mysql_session.context.databases.get_value() if db.name == "testdb")
    yield database
    # Cleanup: drop all tables in testdb
    mysql_session.context.execute("USE testdb")
    mysql_session.context.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in database.tables.get_value():
        mysql_session.context.execute(f"DROP TABLE IF EXISTS `testdb`.`{table.name}`")
    mysql_session.context.execute("SET FOREIGN_KEY_CHECKS = 1")


# Unified fixtures for base test suites
@pytest.fixture
def session(mysql_session):
    """Alias for mysql_session to match base test suite parameter names."""
    return mysql_session


@pytest.fixture
def database(mysql_database):
    """Alias for mysql_database to match base test suite parameter names."""
    return mysql_database


@pytest.fixture
def create_users_table():
    """Provide the create_users_table helper function."""
    return create_users_table_mysql


@pytest.fixture
def datatype_class():
    """Provide the engine-specific datatype class."""
    return MySQLDataType


@pytest.fixture
def indextype_class():
    """Provide the engine-specific indextype class."""
    return MySQLIndexType
