import pytest
from unittest.mock import Mock, patch, call

from structures.engines.sqlite.database import SQLiteDatabase, SQLiteTable, SQLiteIndex, SQLiteColumn
from windows.main.column import TableColumnsController


@pytest.fixture
def mock_table(sqlite_session):
    database = SQLiteDatabase(id=1, name="test_db", context=sqlite_session.context)
    table = SQLiteTable(id=1, name="test_table", database=database)
    table.columns = Mock()
    table.columns.get_value.return_value = [
        SQLiteColumn(id=1, name="col1", table=table, datatype=table.database.context.DATATYPE.VARCHAR),
        SQLiteColumn(id=2, name="col2", table=table, datatype=table.database.context.DATATYPE.VARCHAR),
    ]
    table.indexes = Mock()
    original_indexes = [
        SQLiteIndex(id=1, name="idx_test", type=table.database.context.INDEXTYPE.UNIQUE, columns=["col1"], table=table)
    ]
    table.indexes.get_value.return_value = original_indexes.copy()
    table.indexes.__iter__ = Mock(return_value=iter(original_indexes.copy()))
    table.indexes.append = Mock()
    table.indexes.index = Mock(return_value=0)
    table.copy = Mock(return_value=table)
    return table


@patch('wx.GetApp')
@patch('windows.main.column.CURRENT_SESSION')
@patch('windows.main.column.CURRENT_TABLE')
@patch('windows.main.column.NEW_TABLE')
def test_append_column_index(mock_new_table, mock_current_table, mock_current_session, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_session.get_value.return_value = sqlite_session
    mock_current_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    # Mock the controller and its model
    controller = TableColumnsController(Mock())
    controller.model = Mock()
    controller.model.GetRow.return_value = 1  # second column
    controller.model.data = mock_table.columns.get_value()

    # Mock selected item
    selected = Mock()
    selected.IsOk.return_value = True

    # Existing index
    existing_index = mock_table.indexes.get_value()[0]

    # Call the method
    result = controller.append_column_index(selected, existing_index)

    # Assertions
    assert result is True
    # Check that append was called
    mock_table.indexes.append.assert_called_once_with(existing_index, replace_existing=True)
    assert "col2" in existing_index.columns
    mock_new_table.set_value.assert_called_once_with(mock_table)


@patch('wx.GetApp')
@patch('windows.main.column.CURRENT_SESSION')
@patch('windows.main.column.CURRENT_TABLE')
@patch('windows.main.column.NEW_TABLE')
def test_on_column_insert(mock_new_table, mock_current_table, mock_current_session, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_session.get_value.return_value = sqlite_session
    mock_current_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    list_ctrl = Mock()
    controller = TableColumnsController(list_ctrl)
    controller.model = Mock()
    controller.model.GetItem.return_value = Mock()
    controller._do_edit = Mock()

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    current_column = mock_table.columns.get_value()[0]
    controller.model.get_data_by_item.return_value = current_column

    empty_column = SQLiteColumn(id=3, name="", table=mock_table, datatype=mock_table.database.context.DATATYPE.VARCHAR)
    sqlite_session.context.build_empty_column = Mock(return_value=empty_column)

    mock_table.columns.insert = Mock()
    mock_table.columns.__len__ = Mock(return_value=2)
    mock_table.columns.index = Mock(return_value=0)

    controller.on_column_insert(Mock())

    mock_table.columns.insert.assert_called_once()


@patch('wx.GetApp')
@patch('windows.main.column.CURRENT_SESSION')
@patch('windows.main.column.CURRENT_TABLE')
@patch('windows.main.column.NEW_TABLE')
def test_on_column_delete(mock_new_table, mock_current_table, mock_current_session, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_session.get_value.return_value = sqlite_session
    mock_current_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    list_ctrl = Mock()
    controller = TableColumnsController(list_ctrl)
    controller.model = Mock()

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    column_to_delete = mock_table.columns.get_value()[0]
    controller.model.get_data_by_item.return_value = column_to_delete

    mock_table.columns.remove = Mock()

    index_with_column = Mock()
    index_with_column.columns = Mock()
    index_with_column.columns.__contains__ = Mock(return_value=True)
    index_with_column.columns.remove = Mock()
    index_with_column.columns.__len__ = Mock(return_value=0)
    index_without = Mock()
    index_without.columns = Mock()
    index_without.columns.__contains__ = Mock(return_value=False)
    mock_table.indexes.get_value.return_value = [index_with_column, index_without]
    mock_table.indexes.remove = Mock()

    controller.on_column_delete(Mock())

    mock_table.columns.remove.assert_called_once()
    mock_new_table.set_value.assert_called_once_with(mock_table)


@patch('wx.GetApp')
@patch('windows.main.column.CURRENT_SESSION')
@patch('windows.main.column.CURRENT_TABLE')
@patch('windows.main.column.CURRENT_COLUMN')
@patch('windows.main.column.NEW_TABLE')
def test_on_column_move_up(mock_new_table, mock_current_column, mock_current_table, mock_current_session, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_session.get_value.return_value = sqlite_session
    mock_current_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    list_ctrl = Mock()
    controller = TableColumnsController(list_ctrl)
    controller.model = Mock()

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    selected_column = mock_table.columns.get_value()[1]
    controller.model.get_data_by_item.return_value = selected_column
    controller.model.GetRow.return_value = 1
    controller.model.GetItem.return_value = Mock()

    mock_table.columns.move_up = Mock()

    list_ctrl.Select = Mock()

    controller.on_column_move_up(Mock())

    mock_table.columns.move_up.assert_called_once_with(selected_column)
    list_ctrl.Select.assert_called_once()


@patch('wx.GetApp')
@patch('windows.main.column.CURRENT_SESSION')
@patch('windows.main.column.CURRENT_TABLE')
@patch('windows.main.column.NEW_TABLE')
def test_insert_column_index(mock_new_table, mock_current_table, mock_current_session, mock_get_app, sqlite_session, mock_table):
    mock_get_app.return_value = Mock()
    mock_current_session.get_value.return_value = sqlite_session
    mock_current_table.get_value.return_value = mock_table
    mock_new_table.get_value.return_value = None

    list_ctrl = Mock()
    controller = TableColumnsController(list_ctrl)
    controller.model = Mock()

    selected = Mock()
    selected.IsOk.return_value = True
    list_ctrl.GetSelection.return_value = selected

    selected_column = mock_table.columns.get_value()[0]
    controller.model.get_data_by_item.return_value = selected_column
    controller.model.GetRow.return_value = 0
    controller.model.data = mock_table.columns.get_value()

    mock_table.indexes.append = Mock()
    mock_table.indexes.__iter__ = Mock(return_value=iter([]))  # No existing indexes
    sqlite_session.context.build_empty_index = Mock(return_value=Mock())

    controller.insert_column_index(selected, sqlite_session.context.INDEXTYPE.UNIQUE)

    mock_table.indexes.append.assert_called_once()
    mock_new_table.set_value.assert_called_once_with(mock_table)
