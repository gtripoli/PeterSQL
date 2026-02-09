import pytest
from unittest.mock import Mock, patch, call

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteIndex
from windows.main.index import TableIndexController


@pytest.fixture
def mock_table(sqlite_session):
    database = SQLiteDatabase(id=1, name="test_db", context=sqlite_session.context)
    table = SQLiteTable(id=1, name="test_table", database=database)
    table.indexes = Mock()
    original_indexes = [
        SQLiteIndex(id=1, name="idx_test", type=table.database.context.INDEXTYPE.UNIQUE, columns=["col1"], table=table),
        SQLiteIndex(id=2, name="idx_test2", type=table.database.context.INDEXTYPE.PRIMARY, columns=["id"], table=table)
    ]
    table.indexes.get_value.return_value = original_indexes.copy()
    table.indexes.set_value = Mock()
    table.indexes.remove = Mock()
    table.indexes.clear = Mock()
    table.indexes.__iter__ = Mock(return_value=iter(original_indexes.copy()))
    table.copy = Mock(return_value=table)
    return table


@patch('wx.GetApp')
@patch('windows.main.index.CURRENT_TABLE')
@patch('windows.main.index.CURRENT_INDEX')
def test_on_index_delete(mock_current_index, mock_current_table, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_table.get_value.return_value = mock_table

    list_ctrl = Mock()
    controller = TableIndexController(list_ctrl)
    controller.model = Mock()

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    index_to_delete = mock_table.indexes.get_value()[0]
    controller.model.GetRow.return_value = 0
    controller.model.get_data_by_row.return_value = index_to_delete

    controller.on_index_delete()

    mock_table.indexes.remove.assert_called_once_with(index_to_delete)
    mock_current_table.set_value.assert_called_once_with(mock_table)


@patch('wx.GetApp')
@patch('windows.main.index.CURRENT_TABLE')
@patch('windows.main.index.CURRENT_INDEX')
def test_on_index_clear(mock_current_index, mock_current_table, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_table.get_value.return_value = mock_table

    list_ctrl = Mock()
    controller = TableIndexController(list_ctrl)
    controller.model = Mock()

    controller.on_index_clear()

    controller.model.clear.assert_called_once()
    mock_table.indexes.clear.assert_called_once()
    mock_current_table.set_value.assert_called_once_with(mock_table)
