import sqlite3
import threading
from unittest.mock import Mock, patch

import psycopg2
import pymysql

import pytest

from structures.engines.context import ConnectionLostError, AbstractContext
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration
from structures.session import Session


# ---------------------------------------------------------------------------
# _is_connection_lost() — positive and negative cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exc, expected",
    [
        # PyMySQL InterfaceError → always True
        (pymysql.err.InterfaceError(0, ""), True),
        # PyMySQL OperationalError with disconnect code → True
        (pymysql.err.OperationalError(2006, "MySQL server has gone away"), True),
        (pymysql.err.OperationalError(2013, "Lost connection to MySQL server"), True),
        (pymysql.err.OperationalError(2055, "Lost connection to MySQL server at 'localhost'"), True),
        # PyMySQL OperationalError with disconnect message fragment → True
        (pymysql.err.OperationalError(9999, "server has gone away after reboot"), True),
        # PyMySQL OperationalError with non-disconnect code and no disconnect message → False
        (pymysql.err.OperationalError(1049, "Unknown database 'foo'"), False),
        (pymysql.err.OperationalError(1045, "Access denied for user"), False),
        (pymysql.err.OperationalError(1064, "SQL syntax error"), False),
        # psycopg2 OperationalError with pgcode=None (connection-level) → True
        (psycopg2.OperationalError("server closed the connection unexpectedly"), True),
        # psycopg2 InterfaceError → always True
        (psycopg2.InterfaceError("connection already closed"), True),
        # SQLite disk-level errors → True
        (sqlite3.OperationalError("database is locked"), True),
        (sqlite3.OperationalError("disk I/O error"), True),
        (sqlite3.OperationalError("unable to open database file"), True),
        # SQLite ordinary SQL error → False
        (sqlite3.OperationalError("no such table: foo"), False),
        # Unrelated exception → False
        (ValueError("unexpected"), False),
    ],
)
def test_is_connection_lost_detection(exc, expected):
    assert AbstractContext._is_connection_lost(exc) is expected


def test_psycopg2_operational_error_with_pgcode_is_not_connection_lost():
    """A psycopg2.OperationalError with a pgcode is a server-side SQL error, not
    a lost connection — it must not trigger the reconnection flow."""

    # psycopg2.Error.pgcode is a read-only C property that defaults to None.
    # Use a subclass that overrides it to simulate a server-side error.
    class _AuthError(psycopg2.OperationalError):
        @property
        def pgcode(self) -> str:
            return "28000"  # INVALID_AUTHORIZATION_SPECIFICATION

    exc = _AuthError("FATAL: role \"foo\" does not exist")
    assert AbstractContext._is_connection_lost(exc) is False


def test_pymysql_operational_error_non_disconnect_not_connection_lost():
    """Ordinary PyMySQL OperationalError without disconnect code/message is
    not treated as connection loss."""
    exc = pymysql.err.OperationalError(1146, "Table 'db.missing_table' doesn't exist")
    assert AbstractContext._is_connection_lost(exc) is False


# ---------------------------------------------------------------------------
# execute() integration with the detection logic
# ---------------------------------------------------------------------------

def test_execute_raises_connection_lost_for_sqlite_disk_io():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=2,
        name="sqlite_test",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )

    context = Mock(spec=AbstractContext)
    context.connection = connection
    context.connection.read_only = False
    context.cursor = Mock()
    context.cursor.execute.side_effect = sqlite3.OperationalError("disk I/O error")

    with pytest.raises(ConnectionLostError):
        AbstractContext.execute(context, "SELECT 1")


def test_execute_reraises_non_connection_error():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=3,
        name="sqlite_test",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )

    context = Mock(spec=AbstractContext)
    context.connection = connection
    context.connection.read_only = False
    context.cursor = Mock()
    context.cursor.execute.side_effect = ValueError("syntax error")
    context._is_connection_lost = Mock(return_value=False)

    with pytest.raises(ValueError, match="syntax error"):
        AbstractContext.execute(context, "SELECT 1")


def test_execute_reraises_pymysql_ordinary_operational_error():
    """A non-disconnect PyMySQL OperationalError must not trigger ConnectionLostError."""
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=6,
        name="sqlite_test",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )

    context = Mock(spec=AbstractContext)
    context.connection = connection
    context.connection.read_only = False
    context.cursor = Mock()
    exc = pymysql.err.OperationalError(1146, "Table 'x' doesn't exist")
    context.cursor.execute.side_effect = exc
    # Use the real static method for detection
    context._is_connection_lost = AbstractContext._is_connection_lost

    with pytest.raises(pymysql.err.OperationalError):
        AbstractContext.execute(context, "SELECT 1")


def test_global_connection_lost_handler_is_invoked():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=4,
        name="sqlite_test",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )

    session = Session(connection)
    session.connect()

    handler = Mock()
    session.context.set_connection_lost_handler(handler)

    original_cursor = session.context._cursor
    mock_cursor = Mock()
    mock_cursor.execute.side_effect = sqlite3.OperationalError("disk I/O error")
    session.context._cursor = mock_cursor

    with pytest.raises(ConnectionLostError):
        AbstractContext.execute(session.context, "SELECT 1")

    handler.assert_called_once_with(session.context, "Database connection lost: disk I/O error")
    session.context._cursor = original_cursor
    session.disconnect()


def test_global_connection_lost_handler_is_not_invoked_for_non_connection_error():
    config = SourceConfiguration(filename=":memory:")
    connection = Connection(
        id=5,
        name="sqlite_test",
        engine=ConnectionEngine.SQLITE,
        configuration=config,
    )

    session = Session(connection)
    session.connect()

    handler = Mock()
    session.context.set_connection_lost_handler(handler)

    original_cursor = session.context._cursor
    mock_cursor = Mock()
    mock_cursor.execute.side_effect = ValueError("syntax error")
    session.context._cursor = mock_cursor

    with pytest.raises(ValueError, match="syntax error"):
        AbstractContext.execute(session.context, "SELECT 1")

    handler.assert_not_called()
    session.context._cursor = original_cursor
    session.disconnect()


# ---------------------------------------------------------------------------
# QueryExecutor concurrency guard
# ---------------------------------------------------------------------------

def test_executor_refuses_second_start_while_running():
    """execute_statements() must return early if a worker thread is already alive,
    without mutating _cancel_requested or _loader_context."""
    from windows.main.query.executor import QueryExecutor

    fake_session = Mock()
    executor = QueryExecutor(fake_session)

    # Simulate a running thread
    alive_thread = Mock(spec=threading.Thread)
    alive_thread.is_alive.return_value = True
    executor._current_thread = alive_thread

    on_stmt = Mock()
    on_all = Mock()

    # Should return without starting a new thread or touching loader state
    with patch("windows.main.query.executor.Loader") as mock_loader:
        executor.execute_statements(
            statements=[],
            on_statement_complete=on_stmt,
            on_all_complete=on_all,
        )
        mock_loader.cursor_wait.assert_not_called()

    # Callbacks never called
    on_stmt.assert_not_called()
    on_all.assert_not_called()
    # The existing thread reference is unchanged
    assert executor._current_thread is alive_thread


def test_executor_is_running_reflects_thread_state():
    """is_running() returns True only when _current_thread is alive."""
    from windows.main.query.executor import QueryExecutor

    fake_session = Mock()
    executor = QueryExecutor(fake_session)

    assert executor.is_running() is False

    dead_thread = Mock(spec=threading.Thread)
    dead_thread.is_alive.return_value = False
    executor._current_thread = dead_thread
    assert executor.is_running() is False

    alive_thread = Mock(spec=threading.Thread)
    alive_thread.is_alive.return_value = True
    executor._current_thread = alive_thread
    assert executor.is_running() is True
