import pytest

from structures.session import Session, SessionState
from structures.connection import Connection, ConnectionEngine
from structures.configurations import SourceConfiguration, CredentialsConfiguration


class TestSessionState:
    """Tests for SessionState enum."""

    def test_session_states(self):
        """Test all session states exist."""
        assert SessionState.DISCONNECTED.value == "disconnected"
        assert SessionState.CONNECTING.value == "connecting"
        assert SessionState.CONNECTED.value == "connected"
        assert SessionState.ERROR.value == "error"


class TestSession:
    """Tests for Session class."""

    def test_session_creation(self):
        """Test session creation."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(
            id=1,
            name="test",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )
        session = Session(connection=conn)

        assert session.id == 1
        assert session.connection == conn
        assert session.state == SessionState.DISCONNECTED

    def test_session_set_state(self):
        """Test setting session state."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(
            id=1,
            name="test",
            engine=ConnectionEngine.SQLITE,
            configuration=config,
        )
        session = Session(connection=conn)

        session.set_state(SessionState.CONNECTING)
        assert session.state == SessionState.CONNECTING

        session.set_state(SessionState.CONNECTED)
        assert session.state == SessionState.CONNECTED

    def test_session_equality(self):
        """Test session equality."""
        config = SourceConfiguration(filename=":memory:")
        conn1 = Connection(id=1, name="test", engine=ConnectionEngine.SQLITE, configuration=config)
        conn2 = Connection(id=1, name="test", engine=ConnectionEngine.SQLITE, configuration=config)

        session1 = Session(connection=conn1)
        session2 = Session(connection=conn2)

        assert session1 == session2

    def test_session_inequality(self):
        """Test session inequality."""
        config = SourceConfiguration(filename=":memory:")
        conn1 = Connection(id=1, name="test1", engine=ConnectionEngine.SQLITE, configuration=config)
        conn2 = Connection(id=2, name="test2", engine=ConnectionEngine.SQLITE, configuration=config)

        session1 = Session(connection=conn1)
        session2 = Session(connection=conn2)

        assert session1 != session2

    def test_session_configuration_property(self):
        """Test configuration property."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(id=1, name="test", engine=ConnectionEngine.SQLITE, configuration=config)
        session = Session(connection=conn)

        assert session.configuration == conn.configuration

    def test_session_has_enabled_tunnel(self):
        """Test has_enabled_tunnel method."""
        config = SourceConfiguration(filename=":memory:")
        conn = Connection(id=1, name="test", engine=ConnectionEngine.SQLITE, configuration=config)
        session = Session(connection=conn)

        assert session.has_enabled_tunnel() is False
