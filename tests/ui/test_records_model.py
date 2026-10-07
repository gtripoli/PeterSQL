"""Tests for RecordsModel value access and static-default cache behavior."""
import datetime

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from structures.engines.datatype import DataTypeCategory, SQLDataType

from windows.main.table.records import RecordsModel, _STATIC_DEFAULT_SENTINEL


class TestRecordsModelValueAccess:
    """Verify RecordsModel value access and formatting."""

    @staticmethod
    def _make_column(name: str, datatype: SQLDataType) -> SimpleNamespace:
        return SimpleNamespace(name=name, datatype=datatype)

    def _make_model(self, columns: list[SimpleNamespace], values: dict[str, Any]) -> RecordsModel:
        table = MagicMock()
        table.columns = columns

        record = MagicMock()
        record.values = values

        model = RecordsModel(table, len(columns))
        model._data = [record]
        return model

    def test_valid_column_access_returns_text_value(self):
        column = self._make_column("name", SQLDataType("TEXT", DataTypeCategory.TEXT))
        model = self._make_model([column], {"name": "Alice"})

        assert model.GetValueByRow(0, 0) == "Alice"

    def test_invalid_positive_column_index_returns_empty_string(self):
        model = self._make_model([], {})

        assert model.GetValueByRow(0, 0) == ""

    def test_negative_column_index_returns_empty_string(self):
        column = self._make_column("name", SQLDataType("TEXT", DataTypeCategory.TEXT))
        model = self._make_model([column], {"name": "Alice"})

        assert model.GetValueByRow(0, -1) == ""

    def test_null_value_returns_null_display(self):
        column = self._make_column("name", SQLDataType("TEXT", DataTypeCategory.TEXT))
        model = self._make_model([column], {"name": None})

        assert model.GetValueByRow(0, 0) == "NULL"

    @pytest.mark.parametrize(("value", "expected"), [(0, False), (1, True)])
    def test_boolean_value_returns_boolean(self, value: int, expected: bool):
        column = self._make_column("enabled", SQLDataType("BOOLEAN", DataTypeCategory.INTEGER))
        model = self._make_model([column], {"enabled": value})

        assert model.GetValueByRow(0, 0) is expected

    def test_datetime_value_returns_formatted_datetime(self):
        column = self._make_column("created_at", SQLDataType("DATETIME", DataTypeCategory.TEMPORAL))
        value = datetime.datetime(2026, 6, 23, 14, 5, 6)
        model = self._make_model([column], {"created_at": value})

        assert model.GetValueByRow(0, 0) == "2026-06-23 14:05:06"


class TestIsStaticDefault:
    """Verify the conservative static-default classifier (RecordsModel.is_static_default)."""

    # ---- expressions that MUST be classified as static ----

    @pytest.mark.parametrize("expr", [
        "NULL",
        "null",
        "Null",
        "TRUE",
        "true",
        "FALSE",
        "false",
        "0",
        "1",
        "-1",
        "42",
        "3.14",
        "-0.5",
        "''",                # empty SQL string
        "'hello'",           # simple SQL string
        "'it''s a test'",    # SQL string with escaped single quote
        "'0'",               # string zero
    ])
    def test_static_expressions(self, expr):
        assert RecordsModel.is_static_default(expr) is True, f"{expr!r} should be static"

    # ---- expressions that MUST be classified as dynamic ----

    @pytest.mark.parametrize("expr", [
        "NOW()",
        "CURRENT_TIMESTAMP()",
        "WEEK(CURRENT_TIMESTAMP())",
        "uuid()",
        "rand()",
        "CURRENT_DATE",       # changes daily — conservative: dynamic
        "CURRENT_TIMESTAMP",  # changes — dynamic
        "1 + 1",              # operator expression
        "col_name",           # bare identifier
        "(SELECT 1)",         # subquery
        "UNHEX('00')",        # function call
    ])
    def test_dynamic_expressions(self, expr):
        assert RecordsModel.is_static_default(expr) is False, f"{expr!r} should be dynamic"

    def test_leading_trailing_whitespace_stripped(self):
        """Whitespace around the expression is ignored."""
        assert RecordsModel.is_static_default("  NULL  ") is True
        assert RecordsModel.is_static_default("  42  ") is True
        assert RecordsModel.is_static_default("  'hello'  ") is True

    def test_callable_as_classmethod_or_staticmethod(self):
        """is_static_default can be called both on the class and on an instance."""
        # Via the class (no instance needed)
        assert RecordsModel.is_static_default("NULL") is True
        # Via an instance (staticmethod resolution)
        table = MagicMock()
        table.columns = []
        model = RecordsModel(table, 0)
        assert model.is_static_default("NULL") is True


class TestStaticDefaultSentinel:
    """Verify the sentinel object has the expected identity properties."""

    def test_sentinel_is_not_none(self):
        assert _STATIC_DEFAULT_SENTINEL is not None

    def test_sentinel_is_not_false(self):
        assert _STATIC_DEFAULT_SENTINEL is not False

    def test_sentinel_is_not_zero(self):
        assert _STATIC_DEFAULT_SENTINEL != 0

    def test_sentinel_identity(self):
        """Two references to the sentinel are the same object."""
        from windows.main.table.records import _STATIC_DEFAULT_SENTINEL as s2
        assert _STATIC_DEFAULT_SENTINEL is s2


class TestClearStaticDefaultsCache:
    """Verify that clear_static_defaults_cache invalidates the model cache."""

    def _make_model(self):
        """Return a RecordsModel with a minimal mock table (no columns needed)."""
        table = MagicMock()
        table.columns = []
        return RecordsModel(table, 0)

    def test_cache_starts_empty(self):
        model = self._make_model()
        found, _ = model.get_static_default("col", "0")
        assert found is False

    def test_set_and_get_static_default(self):
        model = self._make_model()
        model.set_static_default("col", "0", 0)
        found, value = model.get_static_default("col", "0")
        assert found is True
        assert value == 0

    def test_clear_removes_entries(self):
        model = self._make_model()
        model.set_static_default("col", "42", 42)
        model.set_static_default("other", "NULL", None)

        model.clear_static_defaults_cache()

        found_col, _ = model.get_static_default("col", "42")
        found_other, _ = model.get_static_default("other", "NULL")
        assert found_col is False
        assert found_other is False

    def test_clear_on_empty_cache_is_safe(self):
        """Clearing an already-empty cache must not raise."""
        model = self._make_model()
        model.clear_static_defaults_cache()  # should not raise
        found, _ = model.get_static_default("col", "0")
        assert found is False

    def test_new_model_starts_with_empty_cache(self):
        """A freshly created RecordsModel never carries over cached values.

        load_model_for() always creates a new RecordsModel, so the static-
        default cache is automatically reset on every table load (including
        after DDL changes that call CURRENT_TABLE.set_value → _on_current_table
        → _load_records_page → load_model_for).
        """
        model_a = self._make_model()
        model_a.set_static_default("col", "0", 999)

        model_b = self._make_model()  # simulates load_model_for on a new table
        found, _ = model_b.get_static_default("col", "0")
        assert found is False, "New model must not inherit cache from a previous model"
