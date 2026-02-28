import pytest
from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SSHTunnelConfiguration

from tests.engines.base_ssh_tests import BaseSSHTunnelTests


@pytest.fixture(scope="module")
def mariadb_ssh_container():
    container = MySqlContainer("mariadb:latest", 
                               name="petersql_test_mariadb_ssh",
                               mem_limit="768m",
                               memswap_limit="1g",
                               nano_cpus=1_000_000_000,
                               shm_size="256m")
    container.with_exposed_ports(22)
    
    with container:
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
def ssh_session(mariadb_ssh_container):
    ssh_config = SSHTunnelConfiguration(
        enabled=True,
        executable="ssh",
        hostname=mariadb_ssh_container.get_container_host_ip(),
        port=mariadb_ssh_container.get_exposed_port(22),
        username="root",
        password="testpassword",
        local_port=0,
    )
    
    db_config = CredentialsConfiguration(
        hostname="127.0.0.1",
        username="root",
        password=mariadb_ssh_container.root_password,
        port=3306,
    )
    
    connection = Connection(
        id=1,
        name="test_ssh_session",
        engine=ConnectionEngine.MARIADB,
        configuration=db_config,
        ssh_tunnel=ssh_config,
    )
    
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.mark.integration
class TestMariaDBSSHTunnel(BaseSSHTunnelTests):
    pass
