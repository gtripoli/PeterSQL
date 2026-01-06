import pytest

from structures.session import Session
from structures.engines import SessionEngine
from structures.configurations import SourceConfiguration


class TestSQLiteContext:
    def test_context_creation(self):
        config = SourceConfiguration(filename=':memory:')
        session = Session(id=1, name='test_session', engine=SessionEngine.SQLITE, configuration=config)

        assert session.context is not None
        assert session.context.session == session
        assert session.context.filename == ':memory:'

    def test_context_connection(self):
        config = SourceConfiguration(filename=':memory:')
        session = Session(id=1, name='test_session', engine=SessionEngine.SQLITE, configuration=config)

        session.context.connect()
        assert session.context._connection is not None

        # Test if we can execute a query
        session.context.execute("SELECT 1 as test")
        result = session.context.fetchone()
        assert result['test'] == 1

        session.context.disconnect()
        assert session.context._connection is None
