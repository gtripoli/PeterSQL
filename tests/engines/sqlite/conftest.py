import pytest

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration

from structures.engines.sqlite.database import SQLiteDatabase


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def sqlite_database(sqlite_session):
    database = SQLiteDatabase(id=1, name="main", context=sqlite_session.context)
    yield database
