import pytest
from unittest.mock import Mock, patch

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable
from windows.main.table.foreign_key import TableForeignKeyController


@pytest.fixture
def mock_table(sqlite_session):
    database = SQLiteDatabase(id=1, name="test_db", context=sqlite_session.context)
    table = SQLiteTable(id=1, name="orders", database=database)
    table.foreign_keys = Mock()
    table.foreign_keys.get_value.return_value = []
    table.foreign_keys.__iter__ = Mock(return_value=iter([]))
    table.foreign_keys.__len__ = Mock(return_value=0)
    table.copy = Mock(return_value=table)
    return table


def _make_fk_controller():
    list_ctrl = Mock()
    with patch('wx.GetApp') as mock_app, \
         patch('windows.main.table.foreign_key.CURRENT_TABLE') as mock_ct, \
         patch('windows.main.table.foreign_key.NEW_TABLE') as mock_nt, \
         patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY'), \
         patch('windows.main.table.foreign_key.CURRENT_SESSION'):
        mock_app.return_value = Mock()
        mock_ct.get_value.return_value = None
        mock_nt.get_value.return_value = None
        controller = TableForeignKeyController(list_ctrl)
    controller.model = Mock()
    return controller, list_ctrl


@patch('windows.main.table.foreign_key.CURRENT_TABLE')
@patch('windows.main.table.foreign_key.NEW_TABLE')
@patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY')
@patch('windows.main.table.foreign_key.CURRENT_SESSION')
def test_on_selection_changed_sets_current_fk(mock_session, mock_cur_fk, mock_new_table, mock_cur_table, mock_table):
    controller, _ = _make_fk_controller()
    mock_cur_table.get_value.return_value = None
    mock_new_table.get_value.return_value = None

    fake_fk = Mock()
    controller.model.get_data_by_item.return_value = fake_fk

    item = Mock()
    item.IsOk.return_value = True
    event = Mock()
    event.GetItem.return_value = item

    controller._on_selection_changed(event)

    mock_cur_fk.set_value.assert_any_call(None)
    mock_cur_fk.set_value.assert_any_call(fake_fk)


@patch('windows.main.table.foreign_key.CURRENT_TABLE')
@patch('windows.main.table.foreign_key.NEW_TABLE')
@patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY')
@patch('windows.main.table.foreign_key.CURRENT_SESSION')
def test_on_selection_changed_invalid_item_only_clears_fk(mock_session, mock_cur_fk, mock_new_table, mock_cur_table):
    controller, _ = _make_fk_controller()

    item = Mock()
    item.IsOk.return_value = False
    event = Mock()
    event.GetItem.return_value = item

    controller._on_selection_changed(event)

    mock_cur_fk.set_value.assert_called_once_with(None)
    controller.model.get_data_by_item.assert_not_called()


@patch('windows.main.table.foreign_key.CURRENT_TABLE')
@patch('windows.main.table.foreign_key.NEW_TABLE')
@patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY')
@patch('windows.main.table.foreign_key.CURRENT_SESSION')
def test_on_fk_delete_removes_fk_from_table(mock_session, mock_cur_fk, mock_new_table, mock_cur_table, mock_table):
    controller, list_ctrl = _make_fk_controller()
    mock_cur_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    fake_fk = Mock()
    controller.model.GetRow.return_value = 0
    controller.model.get_data_by_row.return_value = fake_fk

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    mock_table.foreign_keys.__contains__ = Mock(return_value=True)
    mock_table.foreign_keys.remove = Mock()

    controller.on_foreign_key_delete(Mock())

    mock_table.foreign_keys.remove.assert_called_once_with(fake_fk)
    mock_new_table.set_value.assert_called_once_with(mock_table)


@patch('windows.main.table.foreign_key.CURRENT_TABLE')
@patch('windows.main.table.foreign_key.NEW_TABLE')
@patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY')
@patch('windows.main.table.foreign_key.CURRENT_SESSION')
def test_on_fk_delete_does_nothing_without_selection(mock_session, mock_cur_fk, mock_new_table, mock_cur_table):
    controller, list_ctrl = _make_fk_controller()

    selected = Mock()
    selected.IsOk.return_value = False
    list_ctrl.GetSelection.return_value = selected

    controller.on_foreign_key_delete(Mock())

    mock_new_table.set_value.assert_not_called()


@patch('windows.main.table.foreign_key.CURRENT_TABLE')
@patch('windows.main.table.foreign_key.NEW_TABLE')
@patch('windows.main.table.foreign_key.CURRENT_FOREIGN_KEY')
@patch('windows.main.table.foreign_key.CURRENT_SESSION')
def test_on_fk_clear_empties_table_foreign_keys(mock_session, mock_cur_fk, mock_new_table, mock_cur_table, mock_table):
    controller, _ = _make_fk_controller()
    mock_cur_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    mock_table.foreign_keys.clear = Mock()

    controller.on_foreign_key_clear(Mock())

    controller.model.clear.assert_called_once()
    mock_table.foreign_keys.clear.assert_called_once()
    mock_new_table.set_value.assert_called_once_with(mock_table)
