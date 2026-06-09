import pytest
from unittest.mock import Mock, patch, call

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteView
from windows.main.database.view import ViewEditorController


@pytest.fixture
def mock_parent():
    parent = Mock()
    for name in [
        "rad_view_algorithm_undefined",
        "rad_view_algorithm_merge",
        "rad_view_algorithm_temptable",
        "rad_view_constraint_none",
        "rad_view_constraint_local",
        "rad_view_constraint_cascaded",
        "rad_view_constraint_check_only",
        "rad_view_constraint_read_only",
    ]:
        radio = Mock()
        radio.GetValue.return_value = False
        radio.IsShown.return_value = True
        setattr(parent, name, radio)
    return parent


@pytest.fixture
def new_view(sqlite_session):
    database = SQLiteDatabase(id=1, name="test_db", context=sqlite_session.context)
    return SQLiteView(id=-1, name="new_view", database=database, statement="SELECT 1")


@pytest.fixture
def existing_view(sqlite_session):
    database = SQLiteDatabase(id=1, name="test_db", context=sqlite_session.context)
    return SQLiteView(id=10, name="existing_view", database=database, statement="SELECT 1")


def _make_controller(mock_parent):
    with patch("windows.main.database.view.CURRENT_VIEW") as mock_view_obs, \
         patch("windows.main.database.view.CURRENT_SESSION"), \
         patch("windows.main.database.view.CURRENT_DATABASE"):
        mock_view_obs.get_value.return_value = None
        controller = ViewEditorController(mock_parent)
    return controller


@patch("windows.main.database.view.CURRENT_SESSION")
@patch("windows.main.database.view.CURRENT_DATABASE")
@patch("windows.main.database.view.CURRENT_VIEW")
def test_new_view_has_changes_immediately(mock_view_obs, mock_db, mock_session, mock_parent, new_view):
    mock_view_obs.get_value.return_value = None
    controller = _make_controller(mock_parent)
    assert controller._has_changes(new_view) is True


@patch("windows.main.database.view.CURRENT_SESSION")
@patch("windows.main.database.view.CURRENT_DATABASE")
@patch("windows.main.database.view.CURRENT_VIEW")
def test_new_view_delete_disabled(mock_view_obs, mock_db, mock_session, mock_parent, new_view):
    mock_view_obs.get_value.return_value = new_view
    controller = _make_controller(mock_parent)

    with patch("windows.main.database.view.CURRENT_VIEW") as pv:
        pv.get_value.return_value = new_view
        controller.update_button_states()

    mock_parent.btn_delete_view.Enable.assert_called_with(False)


@patch("windows.main.database.view.CURRENT_SESSION")
@patch("windows.main.database.view.CURRENT_DATABASE")
@patch("windows.main.database.view.CURRENT_VIEW")
def test_existing_view_delete_enabled(mock_view_obs, mock_db, mock_session, mock_parent, existing_view):
    mock_view_obs.get_value.return_value = None
    controller = _make_controller(mock_parent)

    with patch("windows.main.database.view.CURRENT_VIEW") as pv, \
         patch("windows.main.database.view.CURRENT_DATABASE") as pd:
        pv.get_value.return_value = existing_view
        mock_db_instance = Mock()
        mock_db_instance.views = []
        pd.get_value.return_value = mock_db_instance
        controller.update_button_states()

    mock_parent.btn_delete_view.Enable.assert_called_with(True)


@patch("wx.MessageBox")
@patch("windows.main.database.view.CURRENT_SESSION")
@patch("windows.main.database.view.CURRENT_DATABASE")
@patch("windows.main.database.view.CURRENT_VIEW")
def test_save_new_view_calls_save(mock_view_obs, mock_db, mock_session, mock_msgbox, mock_parent, new_view):
    mock_view_obs.get_value.return_value = None
    controller = _make_controller(mock_parent)

    new_view.save = Mock(return_value=True)
    saved = Mock()
    saved.name = new_view.name
    mock_database = Mock()
    mock_database.views = [saved]

    with patch("windows.main.database.view.CURRENT_VIEW") as pv, \
         patch("windows.main.database.view.CURRENT_DATABASE") as pd, \
         patch("windows.main.database.view.CURRENT_SESSION") as ps:
        pv.get_value.return_value = new_view
        pd.get_value.return_value = mock_database
        ps.get_value.return_value = Mock()
        controller.do_save_view()

    new_view.save.assert_called_once()


@patch("wx.MessageBox")
@patch("windows.main.database.view.CURRENT_SESSION")
@patch("windows.main.database.view.CURRENT_DATABASE")
@patch("windows.main.database.view.CURRENT_VIEW")
def test_save_new_view_reloads_from_db(mock_view_obs, mock_db, mock_session, mock_msgbox, mock_parent, new_view):
    mock_view_obs.get_value.return_value = None
    controller = _make_controller(mock_parent)

    new_view.save = Mock(return_value=True)
    saved = Mock()
    saved.name = new_view.name
    mock_database = Mock()
    mock_database.views = [saved]

    with patch("windows.main.database.view.CURRENT_VIEW") as pv, \
         patch("windows.main.database.view.CURRENT_DATABASE") as pd, \
         patch("windows.main.database.view.CURRENT_SESSION") as ps:
        pv.get_value.return_value = new_view
        pd.get_value.return_value = mock_database
        ps.get_value.return_value = Mock()
        controller.do_save_view()

        assert pv.set_value.call_count == 2
        pv.set_value.assert_any_call(None)
        pv.set_value.assert_any_call(saved)
