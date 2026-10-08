"""Tests for the settings dialog UI module (windows/dialogs/settings/controller.py).

These tests exercise the pure Settings data-model logic inside SettingsController
without constructing any real wx dialog or requiring a display connection.
We bypass SettingsController.__init__ by building a minimal fake instance that
has the same attributes (__dict__) the save/load helpers depend on.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from constants import Language, LogLevel
from helpers.settings import Settings
from windows.dialogs.settings.controller import SettingsController


def _make_controller(settings_dict=None):
    """
    Build a SettingsController instance whose __init__ is NOT called,
    so that no real wx.Dialog is created.

    The returned object has `self.settings` and `self.dialog` wired up
    exactly as the real constructor would leave them, using mocks for
    the dialog widgets.
    """
    settings = Settings(settings_dict or {})

    # Create an uninitialised controller instance (no __init__ call)
    ctrl = object.__new__(SettingsController)
    ctrl.settings = settings

    # Build a minimal mock dialog whose widget attributes mirror the real
    # SettingsDialog attribute names referenced in _save_*/_load_* methods.
    dialog = Mock()

    # language combo box
    language_codes = [lang.code for lang in Language]
    dialog.language.GetSelection.return_value = 0
    dialog.language.SetSelection.return_value = None
    dialog.language.FindString.side_effect = lambda s: next(
        (i for i, lang in enumerate(Language) if lang.code == s), -1
    )

    # theme combo box  
    dialog.theme.GetSelection.return_value = -1  # wx.NOT_FOUND
    dialog.theme.GetString.return_value = ""
    dialog.theme.FindString.return_value = -1

    # appearance radio buttons
    dialog.appearance_mode_auto.GetValue.return_value = True
    dialog.appearance_mode_light.GetValue.return_value = False
    dialog.appearance_mode_dark.GetValue.return_value = False

    # advanced fields
    dialog.advanced_connection_timeout.GetValue.return_value = 30
    dialog.advanced_query_timeout.GetValue.return_value = 45
    dialog.advanced_logging_level.GetSelection.return_value = 1  # INFO

    # query editor fields
    dialog.query_editor_statement_separator.GetValue.return_value = ";"
    dialog.query_editor_trim_whitespace.GetValue.return_value = False
    dialog.query_editor_execute_selected_only.GetValue.return_value = False
    dialog.query_editor_autocomplete.GetValue.return_value = True
    dialog.query_editor_format.GetValue.return_value = True

    ctrl.dialog = dialog
    return ctrl, settings


class TestSaveGeneralSettings:
    """Tests for SettingsController._save_general_settings."""

    def test_saves_first_language_code(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.language.GetSelection.return_value = 0

        ctrl._save_general_settings()

        expected_code = list(Language)[0].code
        assert settings.get_value("language") == expected_code

    def test_saves_second_language_code(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.language.GetSelection.return_value = 1  # it_IT

        ctrl._save_general_settings()

        expected_code = list(Language)[1].code
        assert settings.get_value("language") == expected_code

    def test_invalid_selection_defaults_to_en_us(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.language.GetSelection.return_value = 999  # out of range

        ctrl._save_general_settings()

        assert settings.get_value("language") == "en_US"


class TestSaveAdvancedSettings:
    """Tests for SettingsController._save_advanced_settings."""

    def test_saves_connection_timeout(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.advanced_connection_timeout.GetValue.return_value = 120

        ctrl._save_advanced_settings()

        assert settings.get_value("runtime", "connection_timeout") == 120

    def test_saves_query_timeout(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.advanced_query_timeout.GetValue.return_value = 60

        ctrl._save_advanced_settings()

        assert settings.get_value("runtime", "query_timeout") == 60

    def test_saves_logging_level_debug(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.advanced_logging_level.GetSelection.return_value = 0  # DEBUG

        ctrl._save_advanced_settings()

        assert settings.get_value("runtime", "logging_level") == LogLevel.DEBUG.value

    def test_saves_logging_level_info(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.advanced_logging_level.GetSelection.return_value = 1  # INFO

        ctrl._save_advanced_settings()

        assert settings.get_value("runtime", "logging_level") == LogLevel.INFO.value

    def test_out_of_range_level_defaults_to_info(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.advanced_logging_level.GetSelection.return_value = 99

        ctrl._save_advanced_settings()

        assert settings.get_value("runtime", "logging_level") == LogLevel.INFO.value


class TestSaveQueryEditorSettings:
    """Tests for SettingsController._save_query_editor_settings."""

    def test_saves_statement_separator(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.query_editor_statement_separator.GetValue.return_value = "//"

        ctrl._save_query_editor_settings()

        assert settings.get_value("editor", "statement_separator") == "//"

    def test_saves_trim_whitespace_flag(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.query_editor_trim_whitespace.GetValue.return_value = True

        ctrl._save_query_editor_settings()

        assert settings.get_value("editor", "trim_whitespace") is True

    def test_saves_autocomplete_enabled(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.query_editor_autocomplete.GetValue.return_value = False

        ctrl._save_query_editor_settings()

        assert settings.get_value("editor", "autocomplete", "enabled") is False


class TestSaveAppearanceSettings:
    """Tests for SettingsController._save_appearance_settings."""

    def test_saves_auto_appearance_mode(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.appearance_mode_auto.GetValue.return_value = True

        ctrl._save_appearance_settings()

        assert settings.get_value("ui", "appearance", "mode") == "auto"

    def test_saves_light_appearance_mode(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.appearance_mode_auto.GetValue.return_value = False
        ctrl.dialog.appearance_mode_light.GetValue.return_value = True

        ctrl._save_appearance_settings()

        assert settings.get_value("ui", "appearance", "mode") == "light"

    def test_saves_dark_appearance_mode_when_neither_auto_nor_light(self):
        ctrl, settings = _make_controller()
        ctrl.dialog.appearance_mode_auto.GetValue.return_value = False
        ctrl.dialog.appearance_mode_light.GetValue.return_value = False

        ctrl._save_appearance_settings()

        assert settings.get_value("ui", "appearance", "mode") == "dark"


class TestLoadGeneralSettings:
    """Tests for SettingsController._load_general_settings."""

    def test_sets_language_selection_for_en_us(self):
        ctrl, settings = _make_controller({"language": "en_US"})

        ctrl._load_general_settings()

        # en_US is the first Language enum member (index 0)
        ctrl.dialog.language.SetSelection.assert_called_once_with(0)

    def test_sets_language_selection_for_it_it(self):
        ctrl, settings = _make_controller({"language": "it_IT"})

        ctrl._load_general_settings()

        ctrl.dialog.language.SetSelection.assert_called_once_with(1)

    def test_unknown_language_defaults_to_index_0(self):
        ctrl, settings = _make_controller({"language": "xx_XX"})

        ctrl._load_general_settings()

        ctrl.dialog.language.SetSelection.assert_called_once_with(0)
