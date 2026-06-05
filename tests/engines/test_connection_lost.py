import sqlite3
from unittest.mock import Mock

import psycopg2
import pymysql

import pytest

from structures.engines.context import ConnectionLostError, AbstractContext
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration
from structures.session import Session


@pytest.mark.parametrize(
    "exc, expected",
    [
        (pymysql.err.InterfaceError(0, ""), True),
        (pymysql.err.OperationalError(2006, "MySQL server has gone away"), True),
        (psycopg2.OperationalError("server closed the connection unexpectedly"), True),
        (psycopg2.InterfaceError("connection already closed"), True),
        (sqlite3.OperationalError("database is locked"), True),
        (sqlite3.OperationalError("disk I/O error"), True),
        (sqlite3.OperationalError("unable to open database file"), True),
        (sqlite3.OperationalError("no such table: foo"), False),
        (ValueError("unexpected"), False),
    ],
)
def test_is_connection_lost_detection(exc, expected):
    assert AbstractContext._is_connection_lost(exc) is expected


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
