import pytest
import wx

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration


@pytest.fixture(scope="session", autouse=True)
def wx_app():
    """Initialize wx.App for GUI tests"""
    app = wx.App()
    yield app
    app.Destroy()


@pytest.fixture
def sqlite_session():
    """Provide an in-memory SQLite session for tests"""
    config = SourceConfiguration(filename=':memory:')
    connection = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)
    session = Session.from_connection(connection)
    session.connect()
    yield session
    session.disconnect()
