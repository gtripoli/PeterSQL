import pytest
from unittest.mock import Mock, patch

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteView
from windows.main.explorer import TreeExplorerController


def _make_explorer(sessions=None):
    tree_ctrl = Mock()
    tree_ctrl.AddRoot.return_value = Mock()
    tree_ctrl.GetRootItem.return_value = Mock()

    app_mock = Mock()
    app_mock.icon_registry_16.imagelist = Mock()
    app_mock.icon_registry_16.get_index.return_value = 0

    with patch('wx.GetApp', return_value=app_mock), \
         patch('windows.main.explorer.SESSIONS_LIST') as mock_sl, \
         patch('windows.main.explorer.NEW_TABLE') as mock_nt:
        mock_sl.get_value.return_value = sessions or []
        mock_nt.get_value.return_value = None
        controller = TreeExplorerController(tree_ctrl)

    return controller, tree_ctrl


# ---------------------------------------------------------------------------
# reset_current_objects
# ---------------------------------------------------------------------------

@patch('windows.main.explorer.CURRENT_FUNCTION')
@patch('windows.main.explorer.CURRENT_EVENT')
@patch('windows.main.explorer.CURRENT_PROCEDURE')
@patch('windows.main.explorer.CURRENT_TRIGGER')
@patch('windows.main.explorer.CURRENT_VIEW')
@patch('windows.main.explorer.CURRENT_TABLE')
def test_reset_current_objects_clears_all_observables(
        mock_table, mock_view, mock_trigger, mock_proc, mock_event, mock_func):
    controller, _ = _make_explorer()

    controller.reset_current_objects()

    mock_table.set_value.assert_called_once_with(None)
    mock_view.set_value.assert_called_once_with(None)
    mock_trigger.set_value.assert_called_once_with(None)
    mock_proc.set_value.assert_called_once_with(None)
    mock_event.set_value.assert_called_once_with(None)
    mock_func.set_value.assert_called_once_with(None)


# ---------------------------------------------------------------------------
# select_session
# ---------------------------------------------------------------------------

@patch('windows.main.explorer.CURRENT_CONNECTION')
@patch('windows.main.explorer.CURRENT_SESSION')
@patch('windows.main.explorer.CURRENT_DATABASE')
def test_select_session_sets_session_and_connection(mock_db, mock_session, mock_conn, sqlite_session):
    controller, _ = _make_explorer()

    mock_session.get_value.return_value = None
    mock_db.get_value.return_value = None

    event = Mock()
    controller.select_session(sqlite_session, event)

    mock_session.set_value.assert_called_once_with(sqlite_session)
    mock_conn.set_value.assert_called_once_with(sqlite_session.connection)


@patch('windows.main.explorer.CURRENT_CONNECTION')
@patch('windows.main.explorer.CURRENT_SESSION')
@patch('windows.main.explorer.CURRENT_DATABASE')
def test_select_session_skips_if_same_session_and_database(mock_db, mock_session, mock_conn, sqlite_session):
    controller, _ = _make_explorer()

    mock_session.get_value.return_value = sqlite_session
    mock_db.get_value.return_value = Mock()  # Database already selected

    event = Mock()
    controller.select_session(sqlite_session, event)

    mock_session.set_value.assert_not_called()
    event.Skip.assert_called_once()


# ---------------------------------------------------------------------------
# select_sql_object
# ---------------------------------------------------------------------------

@patch('windows.main.explorer.CURRENT_SESSION')
@patch('windows.main.explorer.CURRENT_DATABASE')
@patch('windows.main.explorer.CURRENT_CONNECTION')
@patch('windows.main.explorer.CURRENT_TABLE')
@patch('windows.main.explorer.CURRENT_VIEW')
def test_select_sql_object_table_sets_current_table(
        mock_view, mock_table, mock_conn, mock_db, mock_session, sqlite_session):
    controller, _ = _make_explorer()

    database = SQLiteDatabase(id=1, name="db", context=sqlite_session.context)
    table = SQLiteTable(id=1, name="users", database=database)
    table.copy = Mock(return_value=table)

    mock_session.get_value.return_value = Mock(connection=None)
    mock_conn.get_value.return_value = None
    mock_db.get_value.return_value = database
    mock_table.get_value.return_value = None

    controller.select_sql_object(table)

    mock_table.set_value.assert_called_once_with(table)
    mock_view.set_value.assert_not_called()


@patch('windows.main.explorer.CURRENT_SESSION')
@patch('windows.main.explorer.CURRENT_DATABASE')
@patch('windows.main.explorer.CURRENT_CONNECTION')
@patch('windows.main.explorer.CURRENT_TABLE')
@patch('windows.main.explorer.CURRENT_VIEW')
def test_select_sql_object_view_sets_current_view(
        mock_view, mock_table, mock_conn, mock_db, mock_session, sqlite_session):
    controller, _ = _make_explorer()

    database = SQLiteDatabase(id=1, name="db", context=sqlite_session.context)
    view = SQLiteView(id=1, name="vw_users", database=database, statement="SELECT 1")
    view.copy = Mock(return_value=view)

    mock_session.get_value.return_value = Mock(connection=None)
    mock_conn.get_value.return_value = None
    mock_db.get_value.return_value = database
    mock_view.get_value.return_value = None

    controller.select_sql_object(view)

    mock_view.set_value.assert_called_once_with(view)
    mock_table.set_value.assert_not_called()


@patch('windows.main.explorer.CURRENT_SESSION')
@patch('windows.main.explorer.CURRENT_DATABASE')
@patch('windows.main.explorer.CURRENT_CONNECTION')
@patch('windows.main.explorer.CURRENT_TABLE')
def test_select_sql_object_different_db_updates_current_database(
        mock_table, mock_conn, mock_db, mock_session, sqlite_session):
    controller, _ = _make_explorer()

    old_db = SQLiteDatabase(id=1, name="old_db", context=sqlite_session.context)
    new_db = SQLiteDatabase(id=2, name="new_db", context=sqlite_session.context)
    table = SQLiteTable(id=1, name="users", database=new_db)
    table.copy = Mock(return_value=table)

    session_mock = Mock()
    session_mock.connection = None
    session_mock.context.set_database = Mock()
    mock_session.get_value.return_value = session_mock
    mock_conn.get_value.return_value = None
    mock_db.get_value.return_value = old_db
    mock_table.get_value.return_value = None

    controller.select_sql_object(table)

    mock_db.set_value.assert_called_once_with(new_db)


# ---------------------------------------------------------------------------
# populate_tree
# ---------------------------------------------------------------------------

def test_populate_tree_with_no_sessions_does_not_crash():
    controller, tree_ctrl = _make_explorer(sessions=[])

    tree_ctrl.DeleteAllItems.assert_called()
    tree_ctrl.AddRoot.assert_called_once_with("")
