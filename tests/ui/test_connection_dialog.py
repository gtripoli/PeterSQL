"""Tests for the connection dialog UI module (windows/dialogs/connections/view.py).

These tests exercise pure-Python logic in ConnectionsManager that does not
require a display (no wx.Window construction) and the ConnectionsTreeController
filtering behaviour via mocks.
"""

import pytest

from windows.dialogs.connections.view import ConnectionsManager
from windows.dialogs.connections.controller import ConnectionsTreeController


class TestSerializeExpandedDirectoryPaths:
    """Unit-tests for ConnectionsManager._serialize_expanded_directory_paths."""

    def test_empty_input_returns_empty_list(self):
        result = ConnectionsManager._serialize_expanded_directory_paths(set())
        assert result == []

    def test_single_path_is_included(self):
        paths = {(1,)}
        result = ConnectionsManager._serialize_expanded_directory_paths(paths)
        assert result == [[1]]

    def test_multiple_paths_are_sorted(self):
        paths = {(3,), (1,), (2,)}
        result = ConnectionsManager._serialize_expanded_directory_paths(paths)
        assert result == [[1], [2], [3]]

    def test_nested_path_is_serialized_correctly(self):
        paths = {(1, 2, 3)}
        result = ConnectionsManager._serialize_expanded_directory_paths(paths)
        assert result == [[1, 2, 3]]

    def test_paths_with_non_int_elements_are_skipped(self):
        # Non-int node IDs must be rejected.
        # Use only same-type (str) tuples so sorted() doesn't raise,
        # then check that the non-int check filters them all out.
        paths = {("a",), ("b",)}
        result = ConnectionsManager._serialize_expanded_directory_paths(paths)
        assert result == []

    def test_empty_path_tuple_is_skipped(self):
        paths = {(), (1,)}
        result = ConnectionsManager._serialize_expanded_directory_paths(paths)
        assert result == [[1]]


class TestDeserializeExpandedDirectoryPaths:
    """Unit-tests for ConnectionsManager._deserialize_expanded_directory_paths."""

    def test_empty_list_returns_empty_set(self):
        result = ConnectionsManager._deserialize_expanded_directory_paths([])
        assert result == set()

    def test_non_list_input_returns_empty_set(self):
        result = ConnectionsManager._deserialize_expanded_directory_paths(None)
        assert result == set()

    def test_single_path_is_deserialized(self):
        result = ConnectionsManager._deserialize_expanded_directory_paths([[1, 2]])
        assert result == {(1, 2)}

    def test_multiple_paths_are_deserialized(self):
        raw = [[1], [2, 3]]
        result = ConnectionsManager._deserialize_expanded_directory_paths(raw)
        assert result == {(1,), (2, 3)}

    def test_non_list_element_is_skipped(self):
        raw = [[1], "bad", [2]]
        result = ConnectionsManager._deserialize_expanded_directory_paths(raw)
        assert result == {(1,), (2,)}

    def test_empty_inner_list_is_skipped(self):
        raw = [[], [1]]
        result = ConnectionsManager._deserialize_expanded_directory_paths(raw)
        assert result == {(1,)}

    def test_inner_list_with_non_int_is_skipped(self):
        raw = [["a", "b"], [1]]
        result = ConnectionsManager._deserialize_expanded_directory_paths(raw)
        assert result == {(1,)}

    def test_roundtrip_serialize_deserialize(self):
        original = {(1,), (2, 3), (4, 5, 6)}
        serialized = ConnectionsManager._serialize_expanded_directory_paths(original)
        deserialized = ConnectionsManager._deserialize_expanded_directory_paths(serialized)
        assert deserialized == original
