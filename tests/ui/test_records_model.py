"""Tests for RecordsModel.is_static_default, static-default cache helpers,
and cache invalidation via clear_static_defaults_cache."""
import pytest
from unittest.mock import MagicMock

from windows.main.table.records import RecordsModel, _STATIC_DEFAULT_SENTINEL


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
