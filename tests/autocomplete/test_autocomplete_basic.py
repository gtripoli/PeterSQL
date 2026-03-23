from typing import Optional
from unittest.mock import Mock

from windows.components.stc.autocomplete.auto_complete import (
    SQLAutoCompleteController,
    SQLCompletionProvider,
)
from windows.components.stc.autocomplete.suggestion_builder import SuggestionBuilder
from windows.components.stc.autocomplete.completion_types import CompletionItemType
from windows.components.stc.autocomplete.completion_types import CompletionItem
from windows.components.stc.autocomplete.completion_types import CompletionResult
from windows.state import CURRENT_SESSION


def create_mock_column(col_id: int, name: str, table):
    column = Mock()
    column.id = col_id
    column.name = name
    column.table = table
    column.datatype = None
    return column


def create_mock_table(table_id: int, name: str, database, columns_data):
    table = Mock()
    table.id = table_id
    table.name = name
    table.database = database

    columns = [
        create_mock_column(i, col_name, table)
        for i, col_name in enumerate(columns_data, 1)
    ]
    table.columns = columns

    return table


def create_mock_database():
    context = Mock()
    context.KEYWORDS = [
        "SELECT",
        "FROM",
        "WHERE",
        "INSERT",
        "UPDATE",
        "DELETE",
        "JOIN",
        "ORDER BY",
        "GROUP BY",
        "HAVING",
        "LIMIT",
        "ASC",
        "DESC",
    ]
    context.FUNCTIONS = [
        "COUNT",
        "SUM",
        "AVG",
        "MAX",
        "MIN",
        "UPPER",
        "LOWER",
        "CONCAT",
    ]

    database = Mock()
    database.id = 1
    database.name = "test_db"
    database.context = context

    users_table = create_mock_table(
        1, "users", database, ["id", "name", "email", "created_at", "status"]
    )

    orders_table = create_mock_table(
        2, "orders", database, ["id", "user_id", "total", "status", "created_at"]
    )

    database.tables = [users_table, orders_table]

    return database


def test_empty_context():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="", pos=0)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]
    assert "SELECT" in item_names
    assert "INSERT" in item_names
    assert "UPDATE" in item_names


def test_single_token():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SEL", pos=3)

    assert result is not None
    assert len(result.items) > 0
    assert result.prefix == "SEL"

    item_names = [item.name for item in result.items]
    assert "SELECT" in item_names


def test_select_without_from():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT ", pos=7)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]
    assert "COUNT" in item_names
    assert "SUM" in item_names
    assert "*" in item_names


def test_select_with_from():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT  FROM users", pos=7)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]

    assert "users.id" in item_names
    assert "users.name" in item_names
    assert "COUNT" in item_names


def test_where_basic():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT * FROM users WHERE ", pos=27)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]

    assert "id" in item_names
    assert "name" in item_names
    assert "COUNT" in item_names


def test_from_clause():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT * FROM ", pos=14)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]
    assert "users" in item_names
    assert "orders" in item_names


def test_dot_completion():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT users.", pos=13)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]
    assert "id" in item_names
    assert "name" in item_names
    assert "email" in item_names

    for name in item_names:
        assert "users." not in name


def test_dot_completion_with_prefix_in_select_list():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    result = provider.get(text="SELECT users.na", pos=len("SELECT users.na"))

    assert result is not None
    item_names = [item.name for item in result.items]
    assert item_names == ["name"]


def test_dot_completion_with_prefix_in_where_clause():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    sql = "SELECT * FROM users u WHERE u.em"
    result = provider.get(text=sql, pos=len(sql))

    assert result is not None
    item_names = [item.name for item in result.items]
    assert item_names == ["email"]


def test_dot_completion_with_prefix_in_order_by_clause():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    sql = "SELECT * FROM users u ORDER BY u.na"
    result = provider.get(text=sql, pos=len(sql))

    assert result is not None
    item_names = [item.name for item in result.items]
    assert item_names == ["name"]


def test_non_dot_prefix_keeps_context_suggestions():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    sql = "SELECT * FROM users WHERE na"
    result = provider.get(text=sql, pos=len(sql))

    assert result is not None
    item_names = [item.name for item in result.items]
    assert "name" in item_names
    assert "email" not in item_names


def test_multi_query():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    text = "SELECT * FROM users;\nSELECT * FROM orders WHERE "
    pos = len(text)

    result = provider.get(text=text, pos=pos)

    assert result is not None
    assert len(result.items) > 0

    item_names = [item.name for item in result.items]

    assert "id" in item_names
    assert "user_id" in item_names


def test_clamp_position_boundaries():
    assert SQLCompletionProvider._clamp_position(pos=-1, text="SELECT") == 0
    assert SQLCompletionProvider._clamp_position(pos=999, text="SELECT") == 6
    assert SQLCompletionProvider._clamp_position(pos=3, text="SELECT") == 3


def test_rebuilds_context_detector_when_dialect_changes():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database,
        get_current_table=lambda: None,
    )

    session_mysql = Mock()
    session_mysql.engine.value.dialect = "mysql"

    session_postgresql = Mock()
    session_postgresql.engine.value.dialect = "postgresql"

    try:
        CURRENT_SESSION.set_value(session_mysql)
        first_result = provider.get(text="SEL", pos=3)
        assert first_result is not None
        assert provider._context_detector is not None
        first_detector = provider._context_detector

        CURRENT_SESSION.set_value(session_postgresql)
        second_result = provider.get(text="SEL", pos=3)
        assert second_result is not None
        assert provider._context_detector is not None

        assert provider._context_detector is not first_detector
        assert provider._context_detector._dialect == "postgresql"
    finally:
        CURRENT_SESSION.set_value(None)


def test_unique_items_keeps_same_name_for_different_types():
    items = (
        CompletionItem(name="COUNT", item_type=CompletionItemType.FUNCTION),
        CompletionItem(name="COUNT", item_type=CompletionItemType.KEYWORD),
        CompletionItem(name="COUNT", item_type=CompletionItemType.FUNCTION),
    )

    unique = SQLAutoCompleteController._unique_items(items=items)

    assert unique == [
        CompletionItem(name="COUNT", item_type=CompletionItemType.FUNCTION),
        CompletionItem(name="COUNT", item_type=CompletionItemType.KEYWORD),
    ]


def test_show_respects_min_prefix_length_when_not_forced():
    class DummyEditor:
        @staticmethod
        def GetCurrentPos():
            return 0

        @staticmethod
        def GetText():
            return "a"

    controller = SQLAutoCompleteController.__new__(SQLAutoCompleteController)
    controller._is_enabled = True
    controller._is_showing = False
    controller._editor = DummyEditor()
    controller._provider = Mock()
    controller._min_prefix_length = 2
    controller._current_result = None

    hidden = {"value": False}
    shown_items = []

    controller._hide_popup = lambda: hidden.__setitem__("value", True)
    controller._show_popup = lambda items: shown_items.extend(items)

    controller._provider.get.return_value = CompletionResult(
        prefix="a",
        prefix_length=1,
        items=(CompletionItem(name="alpha", item_type=CompletionItemType.COLUMN),),
    )

    controller.show(force=False)

    assert hidden["value"] is True
    assert shown_items == []


def test_show_ignores_min_prefix_length_when_forced():
    class DummyEditor:
        @staticmethod
        def GetCurrentPos():
            return 0

        @staticmethod
        def GetText():
            return "a"

    controller = SQLAutoCompleteController.__new__(SQLAutoCompleteController)
    controller._is_enabled = True
    controller._is_showing = False
    controller._editor = DummyEditor()
    controller._provider = Mock()
    controller._min_prefix_length = 2
    controller._current_result = None

    hidden = {"value": False}
    shown_items = []

    controller._hide_popup = lambda: hidden.__setitem__("value", True)
    controller._show_popup = lambda items: shown_items.extend(items)

    controller._provider.get.return_value = CompletionResult(
        prefix="a",
        prefix_length=1,
        items=(CompletionItem(name="alpha", item_type=CompletionItemType.COLUMN),),
    )

    controller.show(force=True)

    assert hidden["value"] is False
    assert [item.name for item in shown_items] == ["alpha"]


def test_schema_qualified_from_followup_keywords():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    sql = "SELECT * FROM public.users W"
    result = provider.get(text=sql, pos=len(sql))

    assert result is not None
    assert "WHERE" in [item.name for item in result.items]


def test_quoted_from_followup_keywords():
    database = create_mock_database()
    provider = SQLCompletionProvider(
        get_database=lambda: database, get_current_table=lambda: None
    )

    sql = 'SELECT * FROM "users" '
    result = provider.get(text=sql, pos=len(sql))

    assert result is not None
    assert "WHERE" in [item.name for item in result.items]


def test_schema_qualified_update_target_table_lookup():
    database = create_mock_database()
    builder = SuggestionBuilder(database=database, current_table=None)

    table = builder._find_update_target_table("UPDATE public.users SET na")

    assert table is not None
    assert table.name == "users"


def test_quoted_update_target_table_lookup():
    database = create_mock_database()
    builder = SuggestionBuilder(database=database, current_table=None)

    table = builder._find_update_target_table('UPDATE "users" SET na')

    assert table is not None
    assert table.name == "users"


if __name__ == "__main__":
    test_empty_context()
    test_single_token()
    test_select_without_from()
    test_select_with_from()
    test_where_basic()
    test_from_clause()
    test_dot_completion()
    test_multi_query()

    print("\n✅ All basic autocomplete tests passed!")
