"""Tests for the dataview UI module (windows/components/dataview.py).

These tests exercise pure-Python static methods that do not require a
display or wx widget construction.
"""

import pytest
from unittest.mock import Mock


class TestTableForeignKeysDataViewCtrlStaticMethods:
    """Tests for static helpers on TableForeignKeysDataViewCtrl."""

    def _table_reference_name(self, table):
        """Delegate to the production static method without importing wx widgets."""
        # Import here to defer wx widget import; static method is pure Python.
        from windows.components.dataview import TableForeignKeysDataViewCtrl
        return TableForeignKeysDataViewCtrl._table_reference_name(table)

    def test_table_without_schema_returns_name_only(self):
        table = Mock()
        table.name = "users"
        del table.schema  # ensure getattr returns None
        table.schema = None

        result = self._table_reference_name(table)
        assert result == "users"

    def test_table_with_schema_returns_qualified_name(self):
        table = Mock()
        table.name = "users"
        table.schema = "public"

        result = self._table_reference_name(table)
        assert result == "public.users"

    def test_table_with_empty_schema_returns_name_only(self):
        table = Mock()
        table.name = "orders"
        table.schema = ""

        result = self._table_reference_name(table)
        assert result == "orders"

    def test_table_with_another_schema(self):
        table = Mock()
        table.name = "products"
        table.schema = "inventory"

        result = self._table_reference_name(table)
        assert result == "inventory.products"


class TestQueryEditorResultsDataViewCtrlGetActivatedModelColumn:
    """Tests for _get_activated_model_column without wx widget construction."""

    def _build_ctrl_mock(self, current_column_model=None):
        """Build a mock that mimics QueryEditorResultsDataViewCtrl."""
        from windows.components.dataview import QueryEditorResultsDataViewCtrl

        # We patch only the internal logic we want to test
        ctrl = Mock(spec=QueryEditorResultsDataViewCtrl)

        if current_column_model is not None:
            col_mock = Mock()
            col_mock.GetModelColumn.return_value = current_column_model
            ctrl.CurrentColumn = col_mock
        else:
            ctrl.CurrentColumn = None

        return ctrl

    def test_returns_current_column_when_set(self):
        from windows.components.dataview import QueryEditorResultsDataViewCtrl

        ctrl = self._build_ctrl_mock(current_column_model=3)

        event = Mock()
        event.GetColumn.return_value = 7  # should be ignored

        # Call the unbound method with our mock as self
        result = QueryEditorResultsDataViewCtrl._get_activated_model_column(ctrl, event)
        assert result == 3

    def test_falls_back_to_event_column_when_no_current_column(self):
        from windows.components.dataview import QueryEditorResultsDataViewCtrl

        ctrl = self._build_ctrl_mock(current_column_model=None)

        event = Mock()
        event.GetColumn.return_value = 5

        result = QueryEditorResultsDataViewCtrl._get_activated_model_column(ctrl, event)
        assert result == 5

    def test_returns_none_when_event_column_negative(self):
        from windows.components.dataview import QueryEditorResultsDataViewCtrl

        ctrl = self._build_ctrl_mock(current_column_model=None)

        event = Mock()
        event.GetColumn.return_value = -1

        result = QueryEditorResultsDataViewCtrl._get_activated_model_column(ctrl, event)
        assert result is None
