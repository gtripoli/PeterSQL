import pytest


from testcontainers.postgres import PostgresContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration

POSTGRESQL_VERSIONS: list[str] = [
    "postgres:latest",
    "postgres:16",
    "postgres:15",
]


def pytest_generate_tests(metafunc):
    if "postgresql_version" in metafunc.fixturenames:
        metafunc.parametrize("postgresql_version", POSTGRESQL_VERSIONS)


@pytest.fixture(scope="function")
def postgresql_container(postgresql_version):
    with PostgresContainer(
        postgresql_version,
        name=f"petersql_test_{postgresql_version.replace(':', '_')}",
        mem_limit="512m",
        memswap_limit="768m",
        nano_cpus=1_000_000_000,
        shm_size="128m",
    ) as container:
        yield container


@pytest.fixture(scope="function")
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
