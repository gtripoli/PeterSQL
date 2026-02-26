import pytest


from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration


MYSQL_VERSIONS: list[str] = [
    "mysql:latest",
    "mysql:8.0",
    # "mysql:5.7",  # Disabled: too slow and resource-intensive
]


def pytest_generate_tests(metafunc):
    if "mysql_version" in metafunc.fixturenames:
        metafunc.parametrize("mysql_version", MYSQL_VERSIONS, scope="module")


@pytest.fixture(scope="module")
def mysql_container(mysql_version):
    container = MySqlContainer(mysql_version, name=f"petersql_test_{mysql_version.replace(':', '_')}",
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
