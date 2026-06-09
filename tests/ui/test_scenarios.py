from pathlib import Path
import uuid

import pytest
import wx
from testcontainers.mysql import MySqlContainer

pytestmark = pytest.mark.xdist_group("ui_scenarios")

from constants import WORKDIR
from icons import IconRegistry

from helpers.settings import SettingsRepository

from structures.configurations import CredentialsConfiguration
from structures.connection import ConnectionEngine
from structures.session import Session

from windows.components.stc.profiles import BASE64, CSV, HTML, JSON, MARKDOWN, REGEX, SQL, TEXT, XML, YAML
from windows.components.stc.registry import SyntaxRegistry
from windows.components.stc.styles import apply_stc_theme
from windows.components.stc.styles import set_theme_loader
from windows.components.stc.theme_loader import ThemeLoader
from windows.components.stc.themes import ThemeManager

from windows.dialogs.connections import CURRENT_CONNECTION
from windows.dialogs.connections import CURRENT_DIRECTORY
from windows.dialogs.connections import PENDING_CONNECTION
from windows.dialogs.connections import Connection
from windows.dialogs.connections import ConnectionDirectory
from windows.dialogs.connections.view import ConnectionsManager
from windows.main import CURRENT_COLUMN
from windows.main import CURRENT_DATABASE
from windows.main import CURRENT_EVENT
from windows.main import CURRENT_FOREIGN_KEY
from windows.main import CURRENT_FUNCTION
from windows.main import CURRENT_INDEX
from windows.main import CURRENT_PROCEDURE
from windows.main import CURRENT_RECORDS
from windows.main import CURRENT_SESSION
from windows.main import CURRENT_TABLE
from windows.main import CURRENT_TRIGGER
from windows.main import CURRENT_VIEW
from windows.main import SESSIONS_LIST
from windows.main.controller import MainFrameController

from tests.ui.scenario_helpers import capture_window_screenshot
from tests.ui.scenario_helpers import pump_ui


@pytest.fixture(scope="module")
def scenario_environment(tmp_path_factory):
    import windows.dialogs.connections.repository as repository_module

    monkeypatch = pytest.MonkeyPatch()
    config_root = tmp_path_factory.mktemp("ui_scenarios")
    config_file = config_root / "connections.yml"
    monkeypatch.setattr(
        repository_module,
        "CONNECTIONS_CONFIG_FILE",
        config_file,
    )

    app = wx.GetApp()
    if app is None:
        raise RuntimeError("wx application is not initialized")

    settings_file = config_root / "settings.yml"
    app.settings_repository = SettingsRepository(settings_file)
    app.settings = app.settings_repository.load()

    app.icon_registry_16 = IconRegistry(str(WORKDIR / "icons"), 16)

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

    monkeypatch.undo()


@pytest.fixture(autouse=True)
def cleanup_observables_after_test():
    yield

    # After dialog.Destroy() the C++ widgets are gone but Python callbacks can
    # still be subscribed, causing runtime errors in the next test.
    for obs in (
        CURRENT_DIRECTORY,
        CURRENT_CONNECTION,
        PENDING_CONNECTION,
        CURRENT_SESSION,
        CURRENT_DATABASE,
        CURRENT_TABLE,
        CURRENT_COLUMN,
        CURRENT_INDEX,
        CURRENT_FOREIGN_KEY,
        CURRENT_RECORDS,
        CURRENT_VIEW,
        CURRENT_TRIGGER,
        CURRENT_PROCEDURE,
        CURRENT_FUNCTION,
        CURRENT_EVENT,
    ):
        if obs is CURRENT_RECORDS:
            obs._value = []
        else:
            obs._value = None
        for event_callbacks in obs.callbacks.values():
            event_callbacks.clear()

    SESSIONS_LIST.set_value([])
    for event_callbacks in SESSIONS_LIST.callbacks.values():
        event_callbacks.clear()


def _type_text_with_simulator(control: wx.TextCtrl, value: str) -> None:
    control.SetFocus()
    control.SetValue(value)
    text_event = wx.CommandEvent(wx.EVT_TEXT.typeId, control.GetId())
    text_event.SetEventObject(control)
    control.GetEventHandler().ProcessEvent(text_event)
    pump_ui(5)


def _click_button_with_simulator(button: wx.Button) -> None:
    click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, button.GetId())
    click_event.SetEventObject(button)
    button.GetEventHandler().ProcessEvent(click_event)
    pump_ui(10)


def _click_tool_with_simulator(frame: wx.Frame, tool_id: int) -> None:
    tool_event = wx.CommandEvent(wx.EVT_TOOL.typeId, tool_id)
    tool_event.SetEventObject(frame)
    frame.GetEventHandler().ProcessEvent(tool_event)
    pump_ui(10)


def _set_choice_with_event(control: wx.Choice, value: str) -> None:
    if not control.SetStringSelection(value):
        raise AssertionError(f"Choice value not found: {value}")

    choice_event = wx.CommandEvent(wx.EVT_CHOICE.typeId, control.GetId())
    choice_event.SetEventObject(control)
    control.GetEventHandler().ProcessEvent(choice_event)
    pump_ui(5)


def _set_checkbox_value(checkbox: wx.CheckBox, checked: bool) -> None:
    checkbox.SetFocus()
    checkbox.SetValue(checked)

    check_event = wx.CommandEvent(wx.EVT_CHECKBOX.typeId, checkbox.GetId())
    check_event.SetEventObject(checkbox)
    check_event.SetInt(1 if checked else 0)
    checkbox.GetEventHandler().ProcessEvent(check_event)
    pump_ui(10)


def _rename_current_selection(dialog: ConnectionsManager, target_name: str) -> None:
    item = dialog.connections_tree_ctrl.GetSelection()
    assert item.IsOk()
    obj = dialog.connections_tree_controller.model.ItemToObject(item)
    if isinstance(obj, ConnectionDirectory):
        obj.name = target_name
    else:
        obj.name = target_name
    dialog._on_item_renamed(obj)


def _clear_tree_selection(dialog: ConnectionsManager) -> None:
    dialog.connections_tree_ctrl.UnselectAll()
    CURRENT_DIRECTORY(None)
    CURRENT_CONNECTION(None)
    pump_ui(5)


def _select_directory_by_name(dialog: ConnectionsManager, directory_name: str) -> ConnectionDirectory:
    nodes = dialog._repository.connections.get_value()
    directory = next(
        node
        for node in nodes
        if isinstance(node, ConnectionDirectory) and node.name == directory_name
    )
    item = dialog.connections_tree_controller.model.ObjectToItem(directory)
    assert item.IsOk()
    dialog.connections_tree_ctrl.Select(item)
    dialog.connections_tree_ctrl.EnsureVisible(item)
    CURRENT_DIRECTORY(directory)
    pump_ui(5)
    return directory


def _expand_directory(dialog: ConnectionsManager, directory: ConnectionDirectory) -> None:
    item = dialog.connections_tree_controller.model.ObjectToItem(directory)
    assert item.IsOk()
    dialog.connections_tree_ctrl.Expand(item)
    dialog.connections_tree_ctrl.Select(item)
    dialog.connections_tree_ctrl.EnsureVisible(item)
    CURRENT_DIRECTORY(directory)
    pump_ui(5)


def _is_directory_expanded(dialog: ConnectionsManager, directory: ConnectionDirectory) -> bool:
    item = dialog.connections_tree_controller.model.ObjectToItem(directory)
    assert item.IsOk()
    return bool(dialog.connections_tree_ctrl.IsExpanded(item))


def _get_expanded_paths_from_settings(dialog: ConnectionsManager) -> list[list[int]]:
    value = dialog._app.settings.get_value(
        "ui",
        "dialogs",
        "connections",
        "expanded_directories",
        default=[],
    )
    assert isinstance(value, list)
    return value


def _select_notebook_tab_by_title(notebook: wx.Notebook, title: str) -> None:
    page_count = notebook.GetPageCount()
    for idx in range(page_count):
        if notebook.GetPageText(idx) == title:
            for _ in range(8):
                notebook.SetSelection(idx)
                notebook.ChangeSelection(idx)
                notebook.SetFocus()
                pump_ui(5)

                selected_index = notebook.GetSelection()
                if selected_index == idx and notebook.GetPageText(selected_index) == title:
                    return

            raise AssertionError(f"Failed to keep notebook tab selected: {title}")

    raise AssertionError(f"Notebook tab not found: {title}")


def _find_connection_by_id(dialog: ConnectionsManager, connection_id: int) -> Connection:
    nodes = dialog._repository.connections.get_value()
    return next(
        node
        for node in nodes
        if isinstance(node, Connection) and node.id == connection_id
    )


def _find_child_connection_by_id(
    parent: ConnectionDirectory,
    connection_id: int,
) -> Connection:
    return next(
        child
        for child in parent.children
        if isinstance(child, Connection) and child.id == connection_id
    )


def _select_connection(dialog: ConnectionsManager, connection: Connection) -> None:
    item = dialog.connections_tree_controller.model.ObjectToItem(connection)
    assert item.IsOk()
    dialog.connections_tree_ctrl.Select(item)
    dialog.connections_tree_ctrl.EnsureVisible(item)
    CURRENT_CONNECTION(connection)
    pump_ui(5)


def _prepare_dialog() -> ConnectionsManager:
    CURRENT_DIRECTORY(None)
    CURRENT_CONNECTION(None)
    PENDING_CONNECTION(None)

    dialog = ConnectionsManager(None)
    dialog.SetSize(wx.Size(1100, 780))
    dialog.Show()
    dialog.Raise()
    dialog.SetFocus()
    pump_ui(10)
    return dialog


def test_scenario_a_connection_dialog_root_flow(scenario_environment):
    dialog = _prepare_dialog()
    try:
        _clear_tree_selection(dialog)

        _click_button_with_simulator(dialog.btn_create)
        pump_ui()

        root_connection = CURRENT_CONNECTION()
        assert root_connection is not None
        _type_text_with_simulator(dialog.name, "Scenario Root Connection")
        _type_text_with_simulator(dialog.hostname, "localhost")
        _type_text_with_simulator(dialog.username, "root")
        _type_text_with_simulator(dialog.password, "root")
        _click_button_with_simulator(dialog.btn_save)
        pump_ui(10)

        saved_root_connection = CURRENT_CONNECTION()
        assert saved_root_connection is not None
        root_connection = _find_connection_by_id(dialog, saved_root_connection.id)
        _select_connection(dialog, root_connection)

        _type_text_with_simulator(dialog.hostname, "127.0.0.1")
        _click_button_with_simulator(dialog.btn_save)
        pump_ui(10)

        _click_button_with_simulator(dialog.btn_create_directory)
        pump_ui(10)
        _rename_current_selection(dialog, "Scenario Root Directory")
        pump_ui()

        _select_directory_by_name(dialog, "Scenario Root Directory")
        _click_button_with_simulator(dialog.btn_delete)
        pump_ui(10)

        root_connection = _find_connection_by_id(dialog, root_connection.id)
        _select_connection(dialog, root_connection)
        _click_button_with_simulator(dialog.btn_delete)
        pump_ui(10)

        nodes = dialog._repository.connections.get_value()
        assert not any(
            isinstance(node, ConnectionDirectory) and node.name == "Scenario Root Directory"
            for node in nodes
        )
        assert not any(
            isinstance(node, Connection) and node.name == "Scenario Root Connection"
            for node in nodes
        )
    finally:
        dialog.Destroy()


def test_scenario_b_connection_dialog_nested_flow(refresh_screenshots, scenario_environment):
    dialog = _prepare_dialog()
    try:
        _click_button_with_simulator(dialog.btn_create_directory)
        pump_ui(10)
        _rename_current_selection(dialog, "Scenario Nested Directory")
        pump_ui()

        directory = _select_directory_by_name(dialog, "Scenario Nested Directory")

        _click_button_with_simulator(dialog.btn_create)
        pump_ui()

        connection = CURRENT_CONNECTION()
        assert connection is not None
        _type_text_with_simulator(dialog.name, "Scenario Nested Connection")
        _type_text_with_simulator(dialog.hostname, "localhost")
        _type_text_with_simulator(dialog.username, "root")
        _type_text_with_simulator(dialog.password, "root")
        pump_ui()

        _click_button_with_simulator(dialog.btn_save)
        saved = CURRENT_CONNECTION() is not None and PENDING_CONNECTION() is None
        assert saved is True

        reloaded_directory = _select_directory_by_name(dialog, "Scenario Nested Directory")
        _expand_directory(dialog, reloaded_directory)
        assert _is_directory_expanded(dialog, reloaded_directory) is True
        dialog._save_expanded_directory_paths_to_settings()
        expanded_paths = _get_expanded_paths_from_settings(dialog)
        assert [reloaded_directory.id] in expanded_paths

        saved_nested_connection = CURRENT_CONNECTION()
        assert saved_nested_connection is not None
        nested_connection = _find_child_connection_by_id(
            directory,
            saved_nested_connection.id,
        )
        _select_connection(dialog, nested_connection)
        nested_connection.name = "Scenario Nested Connection Renamed"
        dialog._on_item_renamed(nested_connection)
        pump_ui(10)

        # Reload the renamed connection from repository-backed tree state.
        reloaded_directory = _select_directory_by_name(dialog, "Scenario Nested Directory")
        nested_connection = _find_child_connection_by_id(
            reloaded_directory,
            nested_connection.id,
        )
        _select_connection(dialog, nested_connection)

        _type_text_with_simulator(dialog.hostname, "127.0.0.1")
        _click_button_with_simulator(dialog.btn_save)
        pump_ui(10)

        reloaded_directory = _select_directory_by_name(dialog, "Scenario Nested Directory")
        _expand_directory(dialog, reloaded_directory)

        _click_button_with_simulator(dialog.btn_create)
        pump_ui()

        ssh_connection = CURRENT_CONNECTION()
        assert ssh_connection is not None
        _type_text_with_simulator(dialog.name, "Scenario SSH Tunnel Connection")
        _type_text_with_simulator(dialog.hostname, "localhost")
        _type_text_with_simulator(dialog.username, "root")
        _type_text_with_simulator(dialog.password, "root")
        _set_checkbox_value(dialog.ssh_tunnel_enabled, True)
        assert dialog.connections_model.ssh_tunnel_enabled() is True
        assert dialog.panel_ssh_tunnel.IsEnabled() is True
        _select_notebook_tab_by_title(dialog.m_notebook4, "SSH Tunnel")

        _click_button_with_simulator(dialog.btn_save)
        pump_ui(10)

        if refresh_screenshots:
            _select_notebook_tab_by_title(dialog.m_notebook4, "Settings")
            capture_window_screenshot(
                dialog,
                Path("screenshot") / "connection_dialog_configured.png",
            )

            _select_notebook_tab_by_title(dialog.m_notebook4, "SSH Tunnel")
            capture_window_screenshot(
                dialog,
                Path("screenshot") / "connection_dialog_ssh_tunnel.png",
            )

        pump_ui()

        reloaded_directory = _select_directory_by_name(dialog, "Scenario Nested Directory")
        renamed_nested_connection = _find_child_connection_by_id(
            reloaded_directory,
            nested_connection.id,
        )
        assert renamed_nested_connection.configuration is not None
        assert renamed_nested_connection.configuration.hostname == "127.0.0.1"
    finally:
        dialog.Destroy()


def test_scenario_c_main_window_mysql_container_screenshot(refresh_screenshots, scenario_environment):
    container_name = f"petersql_ui_mysql_{uuid.uuid4().hex[:8]}"
    container = MySqlContainer(
        "mysql:8",
        name=container_name,
        mem_limit="768m",
        memswap_limit="1g",
        nano_cpus=1_000_000_000,
        shm_size="256m",
    )

    with container:
        config = CredentialsConfiguration(
            hostname=container.get_container_host_ip(),
            username="root",
            password=container.root_password,
            port=int(container.get_exposed_port(3306)),
        )
        connection = Connection(
            id=1001,
            name="Scenario MySQL Main Window",
            engine=ConnectionEngine.MYSQL,
            configuration=config,
        )
        session = Session(connection=connection)
        session.connect()

        app = wx.GetApp()
        if app is None:
            raise RuntimeError("wx application is not initialized")

        app.theme_loader = ThemeLoader(WORKDIR / "themes")
        app.theme_loader.load_theme("petersql")
        set_theme_loader(app.theme_loader)

        app.theme_manager = ThemeManager(apply_function=apply_stc_theme)
        app.syntax_registry = SyntaxRegistry([JSON, SQL, XML, YAML, MARKDOWN, HTML, REGEX, CSV, BASE64, TEXT])

        main_frame = MainFrameController()
        main_frame.SetSize(wx.Size(1440, 900))
        main_frame.Show()
        main_frame.Raise()
        main_frame.SetFocus()

        try:
            SESSIONS_LIST.set_value([session])
            CURRENT_SESSION.set_value(session)
            CURRENT_CONNECTION.set_value(connection)

            session.context.databases.refresh()
            first_database = next(iter(session.context.databases.get_value()), None)
            if first_database is not None:
                session.context.set_database(first_database)
                CURRENT_DATABASE.set_value(first_database)

            _click_tool_with_simulator(main_frame, main_frame.tool_add_database.GetId())

            database_name = "ui_mysql_scenario_db"
            _type_text_with_simulator(main_frame.database_name, database_name)

            collation_values = [main_frame.database_collation.GetString(i) for i in range(main_frame.database_collation.GetCount())]
            utf8mb4_collation = next(
                value
                for value in collation_values
                if value.startswith("utf8mb4_general_ci")
            )
            _set_choice_with_event(main_frame.database_collation, utf8mb4_collation)

            _click_button_with_simulator(main_frame.btn_apply_database)
            pump_ui(20)

            session.context.databases.refresh()
            database = next(db for db in session.context.databases.get_value() if db.name == database_name)

            if refresh_screenshots:
                capture_window_screenshot(
                    main_frame,
                    Path("screenshot") / "mysql_main_window_add_database.png",
                )

            assert CURRENT_SESSION.get_value() is session
            current_database = CURRENT_DATABASE.get_value()
            assert current_database is not None
            assert current_database.id == database.id
            assert current_database.name == database.name
        finally:
            main_frame.Destroy()
            session.disconnect()
