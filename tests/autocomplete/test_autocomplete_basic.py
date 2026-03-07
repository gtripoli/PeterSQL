from typing import Optional
from unittest.mock import Mock

from windows.components.stc.autocomplete.auto_complete import SQLCompletionProvider
from windows.components.stc.autocomplete.completion_types import CompletionItemType


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

    print("✓ GT-010 EMPTY context test passed")


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

    print("✓ GT-011 SINGLE_TOKEN test passed")


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

    print("✓ GT-020 SELECT without FROM test passed")


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

    print("✓ GT-021 SELECT with FROM test passed")


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

    print("✓ GT-030 WHERE basic test passed")


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

    print("✓ FROM clause test passed")


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

    print("✓ GT-002 Dot completion test passed")


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

    print("✓ GT-001 Multi-query test passed")


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
