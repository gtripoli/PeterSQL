import pytest

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration

from structures.engines.sqlite.database import SQLiteDatabase


@pytest.fixture(scope="module")
def sqlite_session():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=1,
        name="test_session",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )
    session = Session(connection=connection)
    session.connect()
    yield session
    session.disconnect()


@pytest.fixture(scope="module")
def sqlite_database(sqlite_session):
    # Use the database from context which has proper handlers configured
    databases = sqlite_session.context.get_databases()
    yield databases[0]
