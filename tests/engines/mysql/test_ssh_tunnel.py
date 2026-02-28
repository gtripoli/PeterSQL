import pytest
from testcontainers.mysql import MySqlContainer

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SSHTunnelConfiguration

from tests.engines.base_ssh_tests import BaseSSHTunnelTests


@pytest.fixture(scope="module")
def mysql_ssh_container():
    container = MySqlContainer("mysql:latest", 
                               name="petersql_test_mysql_ssh",
                               mem_limit="768m",
                               memswap_limit="1g",
                               nano_cpus=1_000_000_000,
                               shm_size="256m")
    container.with_exposed_ports(22)
    
    with container:
        install_ssh_commands = [
            "microdnf install -y openssh-server",
            "ssh-keygen -A",
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
def ssh_session(mysql_ssh_container):
    ssh_config = SSHTunnelConfiguration(
        enabled=True,
        executable="ssh",
        hostname=mysql_ssh_container.get_container_host_ip(),
        port=mysql_ssh_container.get_exposed_port(22),
        username="root",
        password="testpassword",
        local_port=0,
    )
    
    db_config = CredentialsConfiguration(
        hostname="127.0.0.1",
        username="root",
        password=mysql_ssh_container.root_password,
        port=3306,
    )
    
    connection = Connection(
        id=1,
        name="test_ssh_session",
        engine=ConnectionEngine.MYSQL,
        configuration=db_config,
        ssh_tunnel=ssh_config,
    )
    
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.mark.ssh
class TestMySQLSSHTunnel(BaseSSHTunnelTests):
    pass
