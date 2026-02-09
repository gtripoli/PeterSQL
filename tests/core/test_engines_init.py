import pytest
from unittest.mock import Mock

from structures.helpers import merge_original_current
from structures.engines.database import SQLColumn, SQLIndex, SQLForeignKey


class TestMergeOriginalCurrent:
    def test_merge_original_modified_columns(self):
        mock_table = Mock()
        original = [
            SQLColumn(id=1, name='col1', table=mock_table, datatype=Mock()),
            SQLColumn(id=2, name='col2', table=mock_table, datatype=Mock()),
        ]
        current = [
            SQLColumn(id=1, name='col1_updated', table=mock_table, datatype=Mock()),
            SQLColumn(id=3, name='col3', table=mock_table, datatype=Mock()),
        ]
        result = merge_original_current(original, current)
        assert len(result) == 3
        assert result[0][0].id == 1  # original col1
        assert result[0][1].id == 1  # current col1
        assert result[1][0] is None  # no original for col3
        assert result[1][1].id == 3  # current col3
        assert result[2][0].id == 2  # original col2
        assert result[2][1] is None  # no current for col2

    def test_merge_original_modified_indexes(self):
        mock_table = Mock()
        mock_type = Mock()
        original = [
            SQLIndex(id=1, name='idx1', type=mock_type, columns=[], table=mock_table),
        ]
        current = [
            SQLIndex(id=1, name='idx1_updated', type=mock_type, columns=[], table=mock_table),
        ]
        result = merge_original_current(original, current)
        assert len(result) == 1
        assert result[0][0].id == 1
        assert result[0][1].id == 1

    def test_merge_original_current_foreign_keys(self):
        mock_table = Mock()
        original = [
            SQLForeignKey(id=1, name='fk1', table=mock_table, columns=[], reference_table='ref1', reference_columns=[], on_update=None, on_delete=None),
        ]
        current = [
            SQLForeignKey(id=1, name='fk1_updated', table=mock_table, columns=[], reference_table='ref1', reference_columns=[], on_update=None, on_delete=None),
        ]
        result = merge_original_current(original, current)
        assert len(result) == 1
        assert result[0][0].id == 1
        assert result[0][1].id == 1
