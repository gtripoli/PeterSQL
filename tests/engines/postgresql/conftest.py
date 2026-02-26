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
    # Expose SSH port
    container.with_exposed_ports(22)
    
    with container:
        # Install and configure SSH in the container
        import logging
        logger = logging.getLogger(__name__)
        
        install_ssh_commands = [
            ["sh", "-c", "apt-get update"],
            ["sh", "-c", "DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server"],
            ["sh", "-c", "mkdir -p /var/run/sshd"],
            ["sh", "-c", "echo 'root:testpassword' | chpasswd"],
            ["sh", "-c", "sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config"],
            ["sh", "-c", "sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config"],
            ["sh", "-c", "nohup /usr/sbin/sshd -D > /dev/null 2>&1 &"],
        ]
        
        for cmd in install_ssh_commands:
            logger.info(f"Executing: {cmd}")
            exit_code, output = container.exec(cmd)
            logger.info(f"Exit code: {exit_code}, Output: {output}")
            if exit_code != 0 and "sshd" not in cmd:
                raise RuntimeError(f"Failed to execute: {cmd}\nExit code: {exit_code}\nOutput: {output}")
        
        # Verify SSH is running
        exit_code, output = container.exec("ps aux | grep sshd")
        logger.info(f"SSH processes: {output}")
        
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
