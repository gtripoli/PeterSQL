import pytest
from unittest.mock import Mock, patch

from windows.main.database.list import (
    ListDatabaseTable,
    ListDatabaseView,
    ListDatabaseProcedure,
    _truncate_statement,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_list_table():
    with patch('windows.main.database.list.CURRENT_DATABASE') as mock_db, \
         patch('windows.main.database.list.CURRENT_TABLE'):
        mock_db.get_value.return_value = None
        controller = ListDatabaseTable(Mock())
    controller.model = Mock()
    controller._app = Mock()  # class attr is None at import time (before wx.App)
    return controller


def _make_list_view():
    with patch('windows.main.database.list.CURRENT_DATABASE') as mock_db, \
         patch('windows.main.database.list.CURRENT_VIEW'):
        mock_db.get_value.return_value = None
        controller = ListDatabaseView(Mock())
    controller.model = Mock()
    controller._app = Mock()
    return controller


def _make_list_procedure():
    with patch('windows.main.database.list.CURRENT_DATABASE') as mock_db, \
         patch('windows.main.database.list.CURRENT_PROCEDURE'):
        mock_db.get_value.return_value = None
        controller = ListDatabaseProcedure(Mock())
    controller.model = Mock()
    return controller


# ---------------------------------------------------------------------------
# _truncate_statement
# ---------------------------------------------------------------------------

def test_truncate_statement_short_returns_as_is():
    assert _truncate_statement("SELECT 1") == "SELECT 1"


def test_truncate_statement_long_appends_ellipsis():
    result = _truncate_statement("A" * 200)
    assert result.endswith("...")
    assert len(result) == 123  # 120 + 3


def test_truncate_statement_empty_returns_empty():
    assert _truncate_statement("") == ""


def test_truncate_statement_collapses_whitespace():
    result = _truncate_statement("SELECT   *   FROM   t")
    assert "  " not in result


# ---------------------------------------------------------------------------
# ListDatabaseTable
# ---------------------------------------------------------------------------

def test_list_table_load_database_calls_set_observable():
    controller = _make_list_table()
    mock_db = Mock()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(mock_db)

    controller.model.set_observable.assert_called_once_with(mock_db.tables)


def test_list_table_load_database_none_does_nothing():
    controller = _make_list_table()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(None)

    controller.model.set_observable.assert_not_called()


def test_list_table_load_database_off_thread_reschedules():
    controller = _make_list_table()
    mock_db = Mock()

    with patch('wx.IsMainThread', return_value=False), \
         patch('wx.CallAfter') as mock_call_after:
        controller._load_database(mock_db)

    mock_call_after.assert_called_once_with(controller._load_database, mock_db)
    controller.model.set_observable.assert_not_called()


def test_list_table_item_activated_sets_current_table():
    controller = _make_list_table()

    mock_table = Mock()
    mock_table.copy.return_value = mock_table
    controller.model.get_data_by_item.return_value = mock_table

    item = Mock()
    item.IsOk.return_value = True
    event = Mock()
    event.GetItem.return_value = item

    with patch('windows.main.database.list.CURRENT_TABLE') as mock_ct, \
         patch('windows.main.database.list.CURRENT_VIEW') as mock_cv:
        controller._on_item_activated(event)

    mock_cv.set_value.assert_called_once_with(None)
    mock_ct.set_value.assert_called_once_with(mock_table)


def test_list_table_item_activated_invalid_item_does_nothing():
    controller = _make_list_table()

    item = Mock()
    item.IsOk.return_value = False
    event = Mock()
    event.GetItem.return_value = item

    with patch('windows.main.database.list.CURRENT_TABLE') as mock_ct:
        controller._on_item_activated(event)

    mock_ct.set_value.assert_not_called()


# ---------------------------------------------------------------------------
# ListDatabaseView
# ---------------------------------------------------------------------------

def test_list_view_load_database_calls_set_observable():
    controller = _make_list_view()
    mock_db = Mock()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(mock_db)

    controller.model.set_observable.assert_called_once_with(mock_db.views)


def test_list_view_load_database_none_does_nothing():
    controller = _make_list_view()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(None)

    controller.model.set_observable.assert_not_called()


def test_list_view_selection_changed_sets_current_view():
    controller = _make_list_view()

    mock_view = Mock()
    mock_view.copy.return_value = mock_view
    controller.model.get_data_by_item.return_value = mock_view

    item = Mock()
    item.IsOk.return_value = True
    event = Mock()
    event.GetItem.return_value = item

    with patch('windows.main.database.list.CURRENT_VIEW') as mock_cv, \
         patch('windows.main.database.list.CURRENT_TABLE') as mock_ct:
        controller._on_selection_changed(event)

    mock_ct.set_value.assert_called_once_with(None)
    mock_cv.set_value.assert_called_once_with(mock_view)


# ---------------------------------------------------------------------------
# ListDatabaseProcedure
# ---------------------------------------------------------------------------

def test_list_procedure_load_database_calls_set_observable():
    controller = _make_list_procedure()
    mock_db = Mock(spec=['procedures'])
    mock_db.procedures = Mock()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(mock_db)

    controller.model.set_observable.assert_called_once_with(mock_db.procedures)


def test_list_procedure_load_database_without_procedures_attr_does_nothing():
    controller = _make_list_procedure()
    mock_db = Mock(spec=[])  # No 'procedures' attribute

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(mock_db)

    controller.model.set_observable.assert_not_called()


def test_list_procedure_load_database_none_does_nothing():
    controller = _make_list_procedure()

    with patch('wx.IsMainThread', return_value=True):
        controller._load_database(None)

    controller.model.set_observable.assert_not_called()


def test_list_procedure_selection_changed_sets_current_procedure():
    controller = _make_list_procedure()

    mock_proc = Mock()
    mock_proc.copy.return_value = mock_proc
    controller.model.get_data_by_item.return_value = mock_proc

    item = Mock()
    item.IsOk.return_value = True
    event = Mock()
    event.GetItem.return_value = item

    with patch('windows.main.database.list.CURRENT_PROCEDURE') as mock_cp, \
         patch('windows.main.database.list.CURRENT_TABLE') as mock_ct, \
         patch('windows.main.database.list.CURRENT_VIEW') as mock_cv:
        controller._on_selection_changed(event)

    mock_ct.set_value.assert_called_once_with(None)
    mock_cv.set_value.assert_called_once_with(None)
    mock_cp.set_value.assert_called_once_with(mock_proc)
