import pytest

from structures.configurations import (
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)


class TestConfigurations:
    def test_credentials_configuration(self):
        config = CredentialsConfiguration(
            hostname="localhost", username="user", password="pass", port=3306
        )
        assert config.hostname == "localhost"
        assert config.username == "user"
        assert config.password == "pass"
        assert config.port == 3306

    def test_source_configuration(self):
        config = SourceConfiguration(filename="/path/to/db.sqlite")
        assert config.filename == "/path/to/db.sqlite"

    def test_ssh_tunnel_configuration(self):
        config = SSHTunnelConfiguration(
            enabled=True,
            executable="ssh",
            hostname="remote.host",
            port=22,
            username="sshuser",
            password="sshpwd",
            local_port=3307,
        )
        assert config.enabled == True
        assert config.executable == "ssh"
        assert config.hostname == "remote.host"
        assert config.port == 22
        assert config.username == "sshuser"
        assert config.password == "sshpwd"
        assert config.local_port == 3307
        assert config.is_enabled == True

    def test_ssh_tunnel_configuration_disabled(self):
        config = SSHTunnelConfiguration(
            enabled=False,
            executable="ssh",
            hostname="remote.host",
            port=22,
            username=None,
            password=None,
            local_port=3307,
        )
        assert config.is_enabled == False

    def test_ssh_tunnel_configuration_supports_remote_target_and_identity(self):
        config = SSHTunnelConfiguration(
            enabled=True,
            executable="ssh",
            hostname="bastion.example.com",
            port=22,
            username="sshuser",
            password=None,
            local_port=0,
            remote_host="db.internal",
            remote_port=3306,
            identity_file="/home/user/.ssh/id_ed25519",
        )

        assert config.is_enabled is True
        assert config.remote_host == "db.internal"
        assert config.remote_port == 3306
        assert config.identity_file == "/home/user/.ssh/id_ed25519"
