import pytest

from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration


class TestConfigurations:
    def test_credentials_configuration(self):
        config = CredentialsConfiguration(
            hostname='localhost',
            username='user',
            password='pass',
            port=3306
        )
        assert config.hostname == 'localhost'
        assert config.username == 'user'
        assert config.password == 'pass'
        assert config.port == 3306

    def test_source_configuration(self):
        config = SourceConfiguration(filename='/path/to/db.sqlite')
        assert config.filename == '/path/to/db.sqlite'

    def test_ssh_tunnel_configuration(self):
        config = SSHTunnelConfiguration(
            enabled=True,
            executable='ssh',
            hostname='remote.host',
            port=22,
            username='sshuser',
            password='sshpwd',
            local_port=3307
        )
        assert config.enabled == True
        assert config.executable == 'ssh'
        assert config.hostname == 'remote.host'
        assert config.port == 22
        assert config.username == 'sshuser'
        assert config.password == 'sshpwd'
        assert config.local_port == 3307
        assert config.is_enabled == True

    def test_ssh_tunnel_configuration_disabled(self):
        config = SSHTunnelConfiguration(
            enabled=False,
            executable='ssh',
            hostname='remote.host',
            port=22,
            username=None,
            password=None,
            local_port=3307
        )
        assert config.is_enabled == False
