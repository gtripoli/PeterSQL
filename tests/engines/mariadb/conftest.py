import pytest


from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration

from structures.engines.mariadb.database import MariaDBDatabase

MARIADB_VERSIONS: list[str] = [
    "mariadb:latest",
    "mariadb:11.8",
    "mariadb:10.11",
    "mariadb:5.5",
]


def pytest_generate_tests(metafunc):
    if "mariadb_version" in metafunc.fixturenames:
        metafunc.parametrize("mariadb_version", MARIADB_VERSIONS)


@pytest.fixture(scope="function")
def mariadb_container(mariadb_version):
    with MySqlContainer(mariadb_version, name=f"petersql_test_{mariadb_version.replace(":", "_")}",
                        mem_limit="768m",
                        memswap_limit="1g",
                        nano_cpus=1_000_000_000,
                        shm_size="256m",
                        ) as container:
        yield container


@pytest.fixture(scope="function")
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
    database = MariaDBDatabase(id=1, name="testdb", context=mariadb_session.context)
    mariadb_session.context.execute("CREATE DATABASE IF NOT EXISTS testdb")
    yield database
