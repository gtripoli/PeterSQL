from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration
from structures.session import Session


class TestConnection:
    def test_sqlite_session_creation(self):
        config = SourceConfiguration(filename=':memory:')
        connection = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)
        session = Session(connection)

        assert session.id == 1
        assert session.name == 'test_session'
        assert session.engine == ConnectionEngine.SQLITE
        assert session.configuration == config
        assert session.context is not None

    def test_session_equality(self):
        config1 = SourceConfiguration(filename='test1.db')
        config2 = SourceConfiguration(filename='test2.db')

        connection1 = Connection(id=1, name='session1', engine=ConnectionEngine.SQLITE, configuration=config1)
        connection2 = Connection(id=1, name='session1', engine=ConnectionEngine.SQLITE, configuration=config1)
        connection3 = Connection(id=2, name='session2', engine=ConnectionEngine.SQLITE, configuration=config2)

        session1 = Session(connection1)
        session2 = Session(connection2)
        session3 = Session(connection3)

        assert session1.connection == session2.connection
        assert session1.connection != session3.connection

    def test_session_with_comments(self):
        config = SourceConfiguration(filename='test.db')
        connection = Connection(
            id=4,
            name='session_with_comments',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            comments='Test session'
        )
        session = Session(connection)

        assert session.connection.comments == 'Test session'

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
        connection = Connection(
            id=5,
            name='session_with_ssh',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            ssh_tunnel=ssh_config
        )
        session = Session(connection)

        assert session.connection.ssh_tunnel == ssh_config

    def test_session_repr(self):
        config = SourceConfiguration(filename='test.db')
        connection = Connection(id=1, name='test', engine=ConnectionEngine.SQLITE, configuration=config)
        session = Session(connection)
        # Test that repr doesn't crash
        repr_str = repr(session)
        assert 'Session' in repr_str
        assert 'test' in repr_str
