import os
import tempfile
from unittest.mock import Mock, patch

from windows.main.query.history import QueryHistoryController


def test_build_query_preview_returns_first_non_empty_line():
    result = QueryHistoryController._build_query_preview("SELECT * FROM users")
    assert result == "SELECT * FROM users"


def test_build_query_preview_skips_blank_lines():
    result = QueryHistoryController._build_query_preview("\n\n  \nSELECT 1")
    assert result == "SELECT 1"


def test_build_query_preview_truncates_at_120_chars():
    long_query = "SELECT " + "x" * 200
    result = QueryHistoryController._build_query_preview(long_query)
    assert len(result) == 120


def test_build_query_preview_empty_content_returns_placeholder():
    result = QueryHistoryController._build_query_preview("")
    assert "(empty query)" in result


def test_build_query_preview_only_whitespace_returns_placeholder():
    result = QueryHistoryController._build_query_preview("   \n   ")
    assert "(empty query)" in result


def test_group_query_paths_by_date_groups_correctly():
    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f1, \
         tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f2:
        path1, path2 = f1.name, f2.name

    try:
        grouped = QueryHistoryController._group_query_paths_by_date([path1, path2])
        all_paths = [p for paths in grouped.values() for p in paths]
        assert path1 in all_paths
        assert path2 in all_paths
    finally:
        os.unlink(path1)
        os.unlink(path2)


def test_group_query_paths_by_date_empty_list_returns_empty():
    grouped = QueryHistoryController._group_query_paths_by_date([])
    assert grouped == {}


def test_refresh_populates_tree_with_sql_files():
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, Mock())

    with tempfile.TemporaryDirectory() as tmpdir:
        sql_file = os.path.join(tmpdir, "q.sql")
        with open(sql_file, "w") as f:
            f.write("SELECT 1")

        with patch.object(controller, '_list_query_paths', return_value=[sql_file]):
            controller.refresh()

    tree_ctrl.DeleteAllItems.assert_called_once()
    tree_ctrl.AppendContainer.assert_called_once()
    tree_ctrl.AppendItem.assert_called_once()


def test_refresh_empty_history_only_clears_tree():
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, Mock())

    with patch.object(controller, '_list_query_paths', return_value=[]):
        controller.refresh()

    tree_ctrl.DeleteAllItems.assert_called_once()
    tree_ctrl.AppendContainer.assert_not_called()


def test_refresh_expands_first_date_group():
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, Mock())

    with tempfile.TemporaryDirectory() as tmpdir:
        sql_file = os.path.join(tmpdir, "q.sql")
        with open(sql_file, "w") as f:
            f.write("SELECT 1")

        with patch.object(controller, '_list_query_paths', return_value=[sql_file]):
            controller.refresh()

    tree_ctrl.Expand.assert_called_once()


def test_open_history_item_calls_callback_for_valid_file():
    on_open = Mock()
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, on_open)

    with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
        path = f.name

    try:
        item = Mock()
        item.IsOk.return_value = True
        tree_ctrl.GetItemData.return_value = path

        controller._open_history_item(item)

        on_open.assert_called_once_with(path)
    finally:
        os.unlink(path)


def test_open_history_item_does_nothing_for_missing_file():
    on_open = Mock()
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, on_open)

    item = Mock()
    item.IsOk.return_value = True
    tree_ctrl.GetItemData.return_value = "/nonexistent/path.sql"

    controller._open_history_item(item)

    on_open.assert_not_called()


def test_open_history_item_does_nothing_when_data_is_not_string():
    on_open = Mock()
    tree_ctrl = Mock()
    controller = QueryHistoryController(tree_ctrl, on_open)

    item = Mock()
    item.IsOk.return_value = True
    tree_ctrl.GetItemData.return_value = 42

    controller._open_history_item(item)

    on_open.assert_not_called()
