import pytest


from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration

MARIADB_VERSIONS: list[str] = [
    "mariadb:latest",
    "mariadb:11.8",
    "mariadb:10.11",
    "mariadb:5.5",
]


def pytest_generate_tests(metafunc):
    if "mariadb_version" in metafunc.fixturenames:
        metafunc.parametrize("mariadb_version", MARIADB_VERSIONS, scope="module")


@pytest.fixture(scope="module")
def mariadb_container(mariadb_version):
    container = MySqlContainer(mariadb_version, name=f"petersql_test_{mariadb_version.replace(":", "_")}",
                        mem_limit="768m",
                        memswap_limit="1g",
                        nano_cpus=1_000_000_000,
                        shm_size="256m",
                        )
    # Expose SSH port
    container.with_exposed_ports(22)
    
    with container:
        # Install and configure SSH in the container
        install_ssh_commands = [
            "apt-get update",
            "apt-get install -y openssh-server",
            "mkdir -p /var/run/sshd",
            "echo 'root:testpassword' | chpasswd",
            "sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config",
            "sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config",
            "/usr/sbin/sshd",
        ]
        
        for cmd in install_ssh_commands:
            exit_code, output = container.exec(cmd)
            if exit_code != 0 and "sshd" not in cmd:
                raise RuntimeError(f"Failed to execute: {cmd}\nOutput: {output}")
        
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
