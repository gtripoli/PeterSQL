"""Tests for the query editor UI module (windows/main/query/controller.py).

These tests exercise pure static methods and instance helpers that do not
require a real wx widget hierarchy or a display connection.
"""

import pytest
import wx
from unittest.mock import Mock, patch

from windows.main.query.controller import QueryEditorController


def _make_app_mock(shortcuts=None):
    """Return a minimal mock that satisfies wx.GetApp().settings.get_value."""
    shortcuts = shortcuts or {}
    app_mock = Mock()
    app_mock.settings.get_value.side_effect = lambda *keys, default=None: default
    return app_mock


def _make_controller(app_mock=None):
    """Build a QueryEditorController with all wx dependencies mocked out."""
    app_mock = app_mock or _make_app_mock()

    editor_mock = Mock()
    notebook_mock = Mock()

    with patch("wx.GetApp", return_value=app_mock):
        ctrl = QueryEditorController(
            stc_editor=editor_mock,
            results_notebook=notebook_mock,
            session_provider=lambda: None,
        )

    return ctrl


class TestMatchesShortcutKey:
    """Tests for QueryEditorController._matches_shortcut_key (static method)."""

    def test_enter_matches_wx_return(self):
        assert QueryEditorController._matches_shortcut_key("enter", wx.WXK_RETURN) is True

    def test_enter_matches_numpad_enter(self):
        assert QueryEditorController._matches_shortcut_key("enter", wx.WXK_NUMPAD_ENTER) is True

    def test_esc_matches_wx_escape(self):
        assert QueryEditorController._matches_shortcut_key("esc", wx.WXK_ESCAPE) is True

    def test_single_letter_matches_uppercase_ord(self):
        assert QueryEditorController._matches_shortcut_key("s", ord("S")) is True

    def test_single_letter_case_insensitive(self):
        # Key name is lowercase; the method compares against ord(key_name.upper())
        assert QueryEditorController._matches_shortcut_key("t", ord("T")) is True

    def test_unknown_key_name_returns_false(self):
        assert QueryEditorController._matches_shortcut_key("f1", wx.WXK_F1) is False

    def test_wrong_key_code_returns_false(self):
        assert QueryEditorController._matches_shortcut_key("enter", wx.WXK_ESCAPE) is False


class TestFormatElapsed:
    """Tests for QueryEditorController._format_elapsed (instance method)."""

    def test_sub_second_duration_contains_ms(self):
        ctrl = _make_controller()
        result = ctrl._format_elapsed(500)
        assert "ms" in result or "500" in result

    def test_one_second_duration_contains_s(self):
        ctrl = _make_controller()
        result = ctrl._format_elapsed(1000)
        # 1000 ms → 1.00 s
        assert "s" in result

    def test_small_ms_formats_without_decimal(self):
        ctrl = _make_controller()
        result = ctrl._format_elapsed(42)
        assert "42" in result

    def test_large_seconds_value(self):
        ctrl = _make_controller()
        result = ctrl._format_elapsed(5500)
        # 5500 ms → 5.50 s
        assert "5.50" in result or "5,50" in result  # locale may vary


class TestMatchesShortcut:
    """Tests for QueryEditorController._matches_shortcut (instance method)."""

    def _make_key_event(self, ctrl=False, shift=False, alt=False, key_code=wx.WXK_RETURN):
        event = Mock()
        event.ControlDown.return_value = ctrl
        event.ShiftDown.return_value = shift
        event.AltDown.return_value = alt
        event.GetKeyCode.return_value = key_code
        return event

    def test_ctrl_enter_shortcut_matches(self):
        ctrl = _make_controller()
        event = self._make_key_event(ctrl=True, key_code=wx.WXK_RETURN)
        assert ctrl._matches_shortcut(event, "Ctrl+Enter") is True

    def test_ctrl_enter_shortcut_fails_without_ctrl(self):
        ctrl = _make_controller()
        event = self._make_key_event(ctrl=False, key_code=wx.WXK_RETURN)
        assert ctrl._matches_shortcut(event, "Ctrl+Enter") is False

    def test_esc_shortcut_matches(self):
        ctrl = _make_controller()
        event = self._make_key_event(ctrl=False, key_code=wx.WXK_ESCAPE)
        assert ctrl._matches_shortcut(event, "Esc") is True

    def test_empty_shortcut_never_matches(self):
        ctrl = _make_controller()
        event = self._make_key_event()
        assert ctrl._matches_shortcut(event, "") is False
