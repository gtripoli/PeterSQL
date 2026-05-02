from pathlib import Path

import pytest
import wx

from windows.dialogs.connections import CURRENT_CONNECTION
from windows.dialogs.connections import CURRENT_DIRECTORY
from windows.dialogs.connections import PENDING_CONNECTION
from windows.dialogs.connections import ConnectionDirectory
from windows.dialogs.connections.view import ConnectionsManager

from tests.ui.scenario_helpers import capture_window_screenshot
from tests.ui.scenario_helpers import pump_ui


class _DummySettings:
    def __init__(self):
        self._data = {}

    def get_value(self, *keys, default=None):
        if not keys:
            return default

        node = self._data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]

        return node

    def set_value(self, *keys, value):
        node = self._data
        for key in keys[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = {}
                node[key] = child
            node = child

        node[keys[-1]] = value


class _DummyIconRegistry:
    imagelist = None

    @staticmethod
    def get_bitmap(_):
        return wx.NullBitmap


@pytest.fixture
def scenario_environment(tmp_path, monkeypatch):
    import windows.dialogs.connections.repository as repository_module

    monkeypatch.setattr(
        repository_module,
        "CONNECTIONS_CONFIG_FILE",
        tmp_path / "connections.yml",
    )

    dummy_app = _DummySettingsApp()
    monkeypatch.setattr(wx, "GetApp", lambda: dummy_app)

    original_message_dialog = wx.MessageDialog

    class _AutoConfirmDialog:
        def __init__(self, *args, **kwargs):
            self._dialog = original_message_dialog(*args, **kwargs)

        def ShowModal(self):
            return wx.ID_YES

        def Destroy(self):
            self._dialog.Destroy()

    monkeypatch.setattr(wx, "MessageDialog", _AutoConfirmDialog)

    yield

    # After dialog.Destroy() the C++ widgets are gone but the dialog's Python
    # callbacks are still subscribed. The next test creates a new dialog that
    # subscribes fresh, but then sets the observables — which fires the destroyed
    # dialog's callbacks too, causing RuntimeError on the deleted wx widgets.
    # Fix: clear both the stored value (silently) and all registered callbacks.
    for obs in (CURRENT_DIRECTORY, CURRENT_CONNECTION, PENDING_CONNECTION):
        obs._value = None
        for event_callbacks in obs.callbacks.values():
            event_callbacks.clear()


class _DummySettingsApp:
    def __init__(self):
        self.settings = _DummySettings()
        self.icon_registry_16 = _DummyIconRegistry()


def _rename_current_selection(dialog: ConnectionsManager, target_name: str) -> None:
    item = dialog.connections_tree_ctrl.GetSelection()
    assert item.IsOk()
    obj = dialog.connections_tree_controller.model.ItemToObject(item)
    if isinstance(obj, ConnectionDirectory):
        obj.name = target_name
    else:
        obj.name = target_name
    dialog._on_item_renamed(obj)


def _prepare_dialog(show: bool = False) -> ConnectionsManager:
    CURRENT_DIRECTORY(None)
    CURRENT_CONNECTION(None)
    PENDING_CONNECTION(None)

    dialog = ConnectionsManager(None)
    dialog.SetSize(wx.Size(1100, 780))
    if show:
        dialog.Show()
    pump_ui()
    return dialog


def test_scenario_connection_dialog_configured(refresh_screenshots, scenario_environment):
    dialog = _prepare_dialog(show=refresh_screenshots)
    try:
        dialog.on_create_directory(None)
        pump_ui()
        _rename_current_selection(dialog, "Scenario Directory")
        pump_ui()

        directory = CURRENT_DIRECTORY()
        assert isinstance(directory, ConnectionDirectory)

        dialog.on_create(None)
        pump_ui()

        connection = CURRENT_CONNECTION()
        assert connection is not None
        connection.name = "Scenario Connection"
        connection.configuration = connection.configuration._replace(
            hostname="localhost",
            username="root",
            password="root",
            port=3306,
        )
        PENDING_CONNECTION(connection)
        pump_ui()

        saved = dialog.on_save(None)
        assert saved is True
        pump_ui()

        refreshed_connection = CURRENT_CONNECTION()
        assert refreshed_connection is not None
        refreshed_connection.name = "Scenario Connection Renamed"
        dialog._on_item_renamed(refreshed_connection)

        if refresh_screenshots:
            capture_window_screenshot(
                dialog,
                Path("screenshot") / "connection_dialog_configured.png",
            )

        pump_ui()

        assert CURRENT_CONNECTION().name == "Scenario Connection Renamed"
    finally:
        dialog.Destroy()


def test_scenario_connection_dialog_tree_state(refresh_screenshots, scenario_environment):
    dialog = _prepare_dialog(show=refresh_screenshots)
    try:
        dialog.on_create_directory(None)
        pump_ui()
        _rename_current_selection(dialog, "Explorer Scenario Directory")
        pump_ui()

        dialog.on_create(None)
        pump_ui()

        connection = CURRENT_CONNECTION()
        assert connection is not None
        connection.name = "Explorer Scenario Connection"
        connection.configuration = connection.configuration._replace(
            hostname="localhost",
            username="root",
            password="root",
        )
        PENDING_CONNECTION(connection)
        pump_ui()

        saved = dialog.on_save(None)
        assert saved is True

        if refresh_screenshots:
            capture_window_screenshot(
                dialog,
                Path("screenshot") / "connection_dialog_explorer_state.png",
            )

        pump_ui()

        item = dialog.connections_tree_ctrl.GetSelection()
        assert item.IsOk()
    finally:
        dialog.Destroy()
