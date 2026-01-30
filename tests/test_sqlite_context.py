import pytest

from structures.session import Connection
from structures.engines import ConnectionEngine
from structures.configurations import SourceConfiguration


class TestSQLiteContext:
    def test_context_creation(self):
        config = SourceConfiguration(filename=':memory:')
        session = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)

        assert session.context is not None
        assert session.context.session == session
        assert session.context.filename == ':memory:'

    def test_context_connection(self):
        config = SourceConfiguration(filename=':memory:')
        session = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)

        session.context.connect()
        assert session.context._connection is not None

        # Test if we can execute a query
        session.context.execute("SELECT 1 as test")
        result = session.context.fetchone()
        assert result['test'] == 1

        session.context.disconnect()
        assert session.context._connection is None
