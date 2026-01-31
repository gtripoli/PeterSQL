import pytest

from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration


class TestSQLiteContext:
    def test_context_creation(self):
        config = SourceConfiguration(filename=':memory:')
        connection = Connection(id=1, name='test_connection', engine=ConnectionEngine.SQLITE, configuration=config)

        assert connection.context is not None
        assert connection.context.connection == connection
        assert connection.context.filename == ':memory:'

    def test_context_connection(self):
        config = SourceConfiguration(filename=':memory:')
        connection = Connection(id=1, name='test_connection', engine=ConnectionEngine.SQLITE, configuration=config)

        connection.context.connect()
        assert connection.context._connection is not None

        # Test if we can execute a query
        connection.context.execute("SELECT 1 as test")
        result = connection.context.fetchone()
        assert result['test'] == 1

        connection.context.disconnect()
        assert connection.context._connection is None
