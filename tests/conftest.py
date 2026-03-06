import pytest
import wx

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration


def _engine_from_nodeid(nodeid: str) -> str | None:
    parts = nodeid.split("/")
    try:
        engines_index = parts.index("engines")
    except ValueError:
        return None

    if engines_index + 1 >= len(parts):
        return None

    return parts[engines_index + 1].lower()


def _variant_from_nodeid(nodeid: str) -> str | None:
    start = nodeid.rfind("[")
    if start == -1:
        return None

    end = nodeid.find("]", start)
    if end == -1:
        return None

    return nodeid[start + 1 : end].lower()


def pytest_collection_modifyitems(config, items):
    for item in items:
        marker = item.get_closest_marker("skip_engine")
        if marker is None:
            continue

        current_engine = _engine_from_nodeid(item.nodeid)
        if current_engine is None:
            continue

        current_variant = _variant_from_nodeid(item.nodeid)

        selectors = {str(arg).lower() for arg in marker.args}
        should_skip = current_engine in selectors
        if not should_skip and current_variant is not None:
            should_skip = current_variant in selectors

        if should_skip:
            item.add_marker(
                pytest.mark.skip(
                    reason=f"{current_engine.capitalize()} has incompatible API for this operation"
                )
            )


@pytest.fixture(scope="session", autouse=True)
def wx_app():
    """Initialize wx.App for GUI tests"""
    app = wx.App()
    yield app
    app.Destroy()


@pytest.fixture
def sqlite_session():
    """Provide an in-memory SQLite session for tests"""
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=1, name="test_session", engine=ConnectionEngine.SQLITE, configuration=config
    )
    session = Session(connection)
    session.connect()
    yield session
    session.disconnect()
