import pytest
import tempfile
import os

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration, CredentialsConfiguration


class TestConnection:
    def test_sqlite_session_creation(self):
        config = SourceConfiguration(filename=':memory:')
        session = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)

        assert session.id == 1
        assert session.name == 'test_session'
        assert session.engine == ConnectionEngine.SQLITE
        assert session.configuration == config
        assert session.context is not None
        assert hasattr(session.context, 'filename')
        assert session.context.filename == ':memory:'

    def test_session_equality(self):
        config1 = SourceConfiguration(filename='test1.db')
        config2 = SourceConfiguration(filename='test2.db')

        session1 = Connection(id=1, name='session1', engine=ConnectionEngine.SQLITE, configuration=config1)
        session2 = Connection(id=1, name='session1', engine=ConnectionEngine.SQLITE, configuration=config1)
        session3 = Connection(id=2, name='session2', engine=ConnectionEngine.SQLITE, configuration=config2)

        assert session1 == session2
        assert session1 != session3

    def test_session_with_comments(self):
        config = SourceConfiguration(filename='test.db')
        session = Connection(
            id=4,
            name='session_with_comments',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            comments='Test session'
        )

        assert session.comments == 'Test session'

    def test_session_with_ssh_tunnel(self):
        from structures.configurations import SSHTunnelConfiguration

        config = SourceConfiguration(filename='test.db')
        ssh_config = SSHTunnelConfiguration(
            enabled=True,
            executable='ssh',
            hostname='remote.host',
            port=22,
            username='sshuser',
            password='sshpwd',
            local_port=3307
        )
        session = Connection(
            id=5,
            name='session_with_ssh',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            ssh_tunnel=ssh_config
        )

        assert session.ssh_tunnel == ssh_config

    def test_session_repr(self):
        config = SourceConfiguration(filename='test.db')
        session = Connection(id=1, name='test', engine=ConnectionEngine.SQLITE, configuration=config)
        # Test that repr doesn't crash
        repr_str = repr(session)
        assert 'Connection' in repr_str
        assert 'test' in repr_str
