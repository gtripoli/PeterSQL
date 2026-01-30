import pytest
import wx

from structures.engines import ConnectionEngine
from structures.connection import Connection
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
    session = Connection(id=1, name='test_session', engine=ConnectionEngine.SQLITE, configuration=config)
    session.context.connect()
    yield session
    session.context.disconnect()
