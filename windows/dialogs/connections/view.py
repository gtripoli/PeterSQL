import dataclasses
import time

from datetime import datetime
from gettext import gettext as _
from typing import Optional

import wx
import wx.dataview

from helpers.loader import Loader
from helpers.logger import logger

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.configurations import CredentialsConfiguration, SourceConfiguration

from windows.views import ConnectionsDialog

from windows.main import CURRENT_SESSION, SESSIONS_LIST

from windows.dialogs.connections import (
    CURRENT_CONNECTION,
    CURRENT_DIRECTORY,
    PENDING_CONNECTION,
    ConnectionDirectory,
)
from windows.dialogs.connections.model import ConnectionModel
from windows.dialogs.connections.controller import ConnectionsTreeController
from windows.dialogs.connections.repository import ConnectionsRepository


class ConnectionsManager(ConnectionsDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self._app = wx.GetApp()
        self._repository = ConnectionsRepository()
        self.engine.SetItems([e.name for e in ConnectionEngine.get_all()])

        self.connections_tree_controller = ConnectionsTreeController(
            self.connections_tree_ctrl, self._repository
        )
        self.connections_tree_controller.on_item_activated = (
            lambda connection: self.on_connect(None)
        )

        self.connections_model = ConnectionModel()
        self.connections_model.bind_controls(
            name=self.name,
            engine=self.engine,
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls_enabled=self.use_tls_enabled,
            filename=self.filename,
            comments=self.comments,
            created_at=self.created_at,
            last_connection_at=self.last_connection_at,
            successful_connected=self.successful_connected,
            unsuccessful_connections=self.unsuccessful_connections,
            last_successful_connection=self.last_successful_connection,
            last_failure_raison=self.last_failure_raison,
            total_connection_attempts=self.total_connection_attempts,
            average_connection_time=self.average_connection_time,
            most_recent_connection_duration=self.most_recent_connection_duration,
            ssh_tunnel_enabled=self.ssh_tunnel_enabled,
            ssh_tunnel_executable=self.ssh_tunnel_executable,
            ssh_tunnel_hostname=self.ssh_tunnel_hostname,
            ssh_tunnel_port=self.ssh_tunnel_port,
            ssh_tunnel_username=self.ssh_tunnel_username,
            ssh_tunnel_password=self.ssh_tunnel_password,
            ssh_tunnel_local_port=self.ssh_tunnel_local_port,
            ssh_tunnel_identity_file=self.identity_file,
            ssh_tunnel_remote_hostname=self.remote_hostname,
            ssh_tunnel_remote_port=self.remote_port,
        )

        self.connections_model.engine.subscribe(self._on_change_engine)
        self.connections_model.ssh_tunnel_enabled.subscribe(self._on_change_ssh_tunnel)

        self._context_menu_item = None
        self._pending_parent_directory_id = None
        self._setup_event_handlers()
        self._update_tree_menu_state()

    def _update_tree_menu_state(self):
        selected_connection = CURRENT_CONNECTION()
        selected_directory = CURRENT_DIRECTORY()

        if self._context_menu_item is not None and self._context_menu_item.IsOk():
            obj = self.connections_tree_controller.model.ItemToObject(
                self._context_menu_item
            )
            if isinstance(obj, Connection):
                selected_connection = obj
                selected_directory = None
            elif isinstance(obj, ConnectionDirectory):
                selected_connection = None
                selected_directory = obj

        self.m_menuItem19.Enable(bool(selected_connection))
        self.m_menuItem18.Enable(bool(selected_connection or selected_directory))

    def _current_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _record_connection_attempt(
        self,
        connection: Connection,
        success: bool,
        duration_ms: int,
        failure_reason: Optional[str] = None,
    ) -> None:
        connection.total_connection_attempts += 1
        connection.last_connection_at = self._current_timestamp()
        connection.most_recent_connection_duration_ms = duration_ms

        if success:
            connection.successful_connections += 1
            connection.last_successful_connection_at = connection.last_connection_at
            connection.last_failure_reason = None
        else:
            connection.unsuccessful_connections += 1
            connection.last_failure_reason = failure_reason or _("Unknown error")

        if connection.total_connection_attempts > 0:
            previous_total = connection.average_connection_time_ms or 0
            attempt_count = connection.total_connection_attempts
            connection.average_connection_time_ms = int(
                ((previous_total * (attempt_count - 1)) + duration_ms) / attempt_count
            )

        if not connection.is_new:
            self._repository.save_connection(connection)

    def _sync_statistics_to_model(self, connection: Connection) -> None:
        self.connections_model.created_at(connection.created_at or "")
        self.connections_model.last_connection_at(connection.last_connection_at or "")
        self.connections_model.successful_connected(
            str(connection.successful_connections)
        )
        self.connections_model.unsuccessful_connections(
            str(connection.unsuccessful_connections)
        )
        self.connections_model.last_successful_connection(
            connection.last_successful_connection_at or ""
        )
        self.connections_model.last_failure_raison(connection.last_failure_reason or "")
        self.connections_model.total_connection_attempts(
            str(connection.total_connection_attempts)
        )
        self.connections_model.average_connection_time(
            str(connection.average_connection_time_ms)
            if connection.average_connection_time_ms is not None
            else ""
        )
        self.connections_model.most_recent_connection_duration(
            str(connection.most_recent_connection_duration_ms)
            if connection.most_recent_connection_duration_ms is not None
            else ""
        )

    def _on_current_directory(self, directory: Optional[ConnectionDirectory]):
        self.btn_delete.Enable(bool(directory))
        self.btn_create_directory.Enable(not bool(directory))
        self._update_tree_menu_state()

    def _on_current_connection(self, connection: Optional[Connection]):
        self.btn_open.Enable(bool(connection and connection.is_valid))
        self.btn_test.Enable(bool(connection and connection.is_valid))
        self.btn_delete.Enable(bool(connection))
        if connection is not None:
            parent_directory = self._repository.find_connection_parent_directory(
                connection.id
            )
            self._pending_parent_directory_id = (
                parent_directory.id if parent_directory else None
            )
            self._sync_statistics_to_model(connection)
        self._update_tree_menu_state()

    def _on_pending_connection(self, connection: Connection):
        if connection is None:
            self.btn_save.Enable(False)
            current = CURRENT_CONNECTION()
            self.btn_test.Enable(bool(current and current.is_valid))
            self.btn_open.Enable(bool(current and current.is_valid))
            return

        item = self.connections_tree_controller.model.ObjectToItem(connection)
        if item.IsOk():
            self.connections_tree_controller.model.ItemChanged(item)

        self.btn_save.Enable(bool(connection and connection.is_valid))
        self.btn_test.Enable(bool(connection and connection.is_valid))
        self.btn_open.Enable(bool(connection and connection.is_valid))

    def _on_connection_activated(self, connection: Connection):
        CURRENT_CONNECTION(connection)
        self.on_connect(None)

    def _on_change_engine(self, value: str):
        connection_engine = ConnectionEngine.from_name(value)

        self.panel_credentials.Show(
            connection_engine
            in [
                ConnectionEngine.MYSQL,
                ConnectionEngine.MARIADB,
                ConnectionEngine.POSTGRESQL,
            ]
        )
        self.panel_ssh_tunnel.Show(
            connection_engine
            in [
                ConnectionEngine.MYSQL,
                ConnectionEngine.MARIADB,
                ConnectionEngine.POSTGRESQL,
            ]
        )

        self.panel_source.Show(connection_engine == ConnectionEngine.SQLITE)

        self.panel_source.GetParent().Layout()

    def _on_change_ssh_tunnel(self, enable: bool):
        self.panel_ssh_tunnel.Show(enable)
        self.panel_ssh_tunnel.Enable(enable)
        self.panel_ssh_tunnel.GetParent().Layout()

    def _on_search_changed(self, event):
        search_text = self.search_connection.GetValue()
        self.connections_tree_controller.do_filter_connections(search_text)

    def _setup_event_handlers(self):
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        self.search_connection.Bind(wx.EVT_TEXT, self._on_search_changed)
        self.connections_tree_ctrl.Bind(
            wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU,
            self._on_tree_item_context_menu,
        )

        CURRENT_DIRECTORY.subscribe(self._on_current_directory)
        CURRENT_CONNECTION.subscribe(self._on_current_connection)
        PENDING_CONNECTION.subscribe(self._on_pending_connection)

    def _on_tree_item_context_menu(self, event):
        position = event.GetPosition()
        if position == wx.DefaultPosition:
            position = self.connections_tree_ctrl.ScreenToClient(wx.GetMousePosition())

        if isinstance(position, tuple):
            position = wx.Point(position[0], position[1])

        self._show_tree_menu(position)

    def _show_tree_menu(self, position: wx.Point):
        if position.x < 0 or position.y < 0:
            position = wx.Point(8, 8)

        self._context_menu_item, _ = self.connections_tree_ctrl.HitTest(position)

        self._update_tree_menu_state()
        self.connections_tree_ctrl.PopupMenu(self.connection_tree_menu, position)
        self._context_menu_item = None

    def _get_action_item(self):
        if self._context_menu_item is not None and self._context_menu_item.IsOk():
            return self._context_menu_item

        selected_item = self.connections_tree_ctrl.GetSelection()
        if selected_item is not None and selected_item.IsOk():
            return selected_item

        return None

    def _capture_expanded_directory_paths(self):
        expanded_paths = set()

        def _walk(nodes, parent_path=()):
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    path = parent_path + (node.id,)
                    item = self.connections_tree_controller.model.ObjectToItem(node)
                    if (
                        item is not None
                        and item.IsOk()
                        and self.connections_tree_ctrl.IsExpanded(item)
                    ):
                        expanded_paths.add(path)
                    _walk(node.children, path)

        _walk(self._repository.connections.get_value())
        return expanded_paths

    def _restore_expanded_directory_paths(self, expanded_paths):
        if not expanded_paths:
            return

        def _walk(nodes, parent_path=()):
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    path = parent_path + (node.id,)
                    if path in expanded_paths:
                        item = self.connections_tree_controller.model.ObjectToItem(node)
                        if item is not None and item.IsOk():
                            self.connections_tree_ctrl.Expand(item)
                    _walk(node.children, path)

        _walk(self._repository.connections.get_value())

    def do_open_session(self, session: Session):
        # CONNECTIONS_LIST.append(connection)

        SESSIONS_LIST.append(session)
        CURRENT_SESSION(session)

        if not self.GetParent():
            # CURRENT_CONNECTION(connection)
            self._app.open_main_frame()

        self.Hide()

    def on_test_session(self, *args):
        connection = CURRENT_CONNECTION()

        session = Session(connection)

        try:
            self.verify_session(session)
        except Exception as ex:
            pass
        else:
            wx.MessageDialog(
                None,
                message=_("Connection established successfully"),
                caption=_("Connection"),
                style=wx.OK,
            ).ShowModal()

    def on_save(self, *args):
        connection = PENDING_CONNECTION.get_value()
        if not connection:
            return False

        dialog = wx.MessageDialog(
            None,
            message=_(f"Do you want save the connection {connection.name}?"),
            caption=_("Confirm save"),
            style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
        )

        if dialog.ShowModal() != wx.ID_YES:
            return False

        expanded_paths = self._capture_expanded_directory_paths()

        if not connection.created_at:
            connection.created_at = self._current_timestamp()

        parent_obj = None
        parent_item = None
        if isinstance(connection.parent, ConnectionDirectory):
            parent_obj = connection.parent
            parent_item = self.connections_tree_controller.model.ObjectToItem(
                parent_obj
            )
        elif self._pending_parent_directory_id is not None:
            parent_obj = self._find_directory_by_id(self._pending_parent_directory_id)
            if parent_obj is not None:
                parent_item = self.connections_tree_controller.model.ObjectToItem(
                    parent_obj
                )

        if connection.is_new:
            self._repository.add_connection(connection, parent_obj)
        else:
            self._repository.save_connection(connection)

        refreshed_connection = self._find_connection_by_id(connection.id)

        PENDING_CONNECTION(None)

        if refreshed_connection is None:
            refreshed_connection = connection

        CURRENT_CONNECTION(refreshed_connection)

        wx.CallAfter(self._restore_expanded_directory_paths, expanded_paths)
        wx.CallAfter(self._select_connection_in_tree, refreshed_connection, parent_item)

        return True

    def _confirm_save_pending_changes(self) -> bool:
        if PENDING_CONNECTION() is None:
            return True

        dialog = wx.MessageDialog(
            None,
            message=_(
                "You have unsaved changes. Do you want to save them before continuing?"
            ),
            caption=_("Unsaved changes"),
            style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION,
        )
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_YES:
            return bool(self.on_save(None))

        if result == wx.ID_NO:
            PENDING_CONNECTION(None)
            return True

        return False

    def _get_selected_parent_directory(self) -> Optional[ConnectionDirectory]:
        selected_item = self.connections_tree_ctrl.GetSelection()
        if not selected_item.IsOk():
            return None

        selected_obj = self.connections_tree_controller.model.ItemToObject(
            selected_item
        )
        if isinstance(selected_obj, ConnectionDirectory):
            return selected_obj

        if isinstance(selected_obj, Connection):
            parent_item = self.connections_tree_controller.model.GetParent(
                selected_item
            )
            if parent_item and parent_item.IsOk():
                parent_obj = self.connections_tree_controller.model.ItemToObject(
                    parent_item
                )
                if isinstance(parent_obj, ConnectionDirectory):
                    return parent_obj

        return None

    def _create_connection(self):
        if not self._confirm_save_pending_changes():
            return

        selected_engine_name = self.engine.GetStringSelection() or "MySQL"
        engine = ConnectionEngine.from_name(selected_engine_name)
        if engine == ConnectionEngine.POSTGRESQL:
            port = 5432
        elif engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB]:
            port = 3306
        else:
            port = 3306

        if engine in [
            ConnectionEngine.MYSQL,
            ConnectionEngine.MARIADB,
            ConnectionEngine.POSTGRESQL,
        ]:
            configuration = CredentialsConfiguration(
                hostname="localhost",
                username="root",
                password="",
                port=port,
            )
        else:
            configuration = SourceConfiguration(filename="")

        new_connection = Connection(
            id=-1,
            name=self._generate_unique_new_connection_name(),
            engine=engine,
            configuration=configuration,
            comments="",
            ssh_tunnel=None,
        )

        expanded_paths = self._capture_expanded_directory_paths()
        parent = self._get_selected_parent_directory()
        self._pending_parent_directory_id = parent.id if parent else None
        self._repository.add_connection(new_connection, parent)

        refreshed_connection = self._find_connection_by_id(new_connection.id)
        if refreshed_connection is None:
            refreshed_connection = new_connection

        CURRENT_CONNECTION(refreshed_connection)
        PENDING_CONNECTION(None)
        wx.CallAfter(self._restore_expanded_directory_paths, expanded_paths)
        wx.CallAfter(self._select_connection_in_tree, refreshed_connection)
        wx.CallAfter(self.on_rename, None)

    def on_create(self, event):
        self._create_connection()

    def on_new_connection(self, event):
        self._create_connection()

    def _find_connection_by_id(self, connection_id: int) -> Optional[Connection]:
        def _search(nodes):
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    found = _search(node.children)
                    if found:
                        return found
                    continue

                if isinstance(node, Connection) and node.id == connection_id:
                    return node

            return None

        return _search(self._repository.connections.get_value())

    def _find_directory_by_id(self, directory_id: int) -> Optional[ConnectionDirectory]:
        def _search(nodes):
            for node in nodes:
                if not isinstance(node, ConnectionDirectory):
                    continue

                if node.id == directory_id:
                    return node

                found = _search(node.children)
                if found:
                    return found

            return None

        return _search(self._repository.connections.get_value())

    def _generate_unique_new_connection_name(self) -> str:
        base_name = _("New connection")
        existing_names = self._repository.get_all_connection_names()
        if base_name not in existing_names:
            return base_name

        index = 1
        while True:
            candidate = f"{base_name}({index})"
            if candidate not in existing_names:
                return candidate
            index += 1

    def _expand_item_parents(self, item):
        parent = self.connections_tree_controller.model.GetParent(item)
        while parent is not None and parent.IsOk():
            self.connections_tree_ctrl.Expand(parent)
            parent = self.connections_tree_controller.model.GetParent(parent)

    def _select_connection_in_tree(
        self,
        connection: Connection,
        parent_item=None,
    ):
        item = self.connections_tree_controller.model.ObjectToItem(connection)
        if item is None or not item.IsOk():
            return

        if parent_item is not None and parent_item.IsOk():
            self.connections_tree_ctrl.Expand(parent_item)

        self._expand_item_parents(item)
        self.connections_tree_ctrl.Select(item)
        self.connections_tree_ctrl.EnsureVisible(item)

    def on_create_directory(self, event):
        if not self._confirm_save_pending_changes():
            return

        parent = self._get_selected_parent_directory()
        expanded_paths = self._capture_expanded_directory_paths()
        new_dir = ConnectionDirectory(id=-1, name=_("New directory"))
        self._repository.add_directory(new_dir, parent)

        item = self.connections_tree_controller.model.ObjectToItem(new_dir)
        if item.IsOk():
            self.connections_tree_ctrl.Select(item)
            self.connections_tree_controller.edit_item(item)

        if parent:
            parent_item = self.connections_tree_controller.model.ObjectToItem(parent)
            self.connections_tree_ctrl.Expand(parent_item)

        wx.CallAfter(self._restore_expanded_directory_paths, expanded_paths)

    def on_new_directory(self, event):
        self.on_create_directory(event)

    def _generate_clone_name(self, base_name: str) -> str:
        existing_names = set()

        def _collect(nodes):
            for node in nodes:
                if isinstance(node, ConnectionDirectory):
                    _collect(node.children)
                elif isinstance(node, Connection):
                    existing_names.add(node.name)

        _collect(self._repository.connections.get_value())

        idx = 1
        while True:
            candidate = f"{base_name}(clone)({idx})"
            if candidate not in existing_names:
                return candidate
            idx += 1

    def on_clone_connection(self, event):
        selected_item = self._get_action_item()
        if selected_item is None or not selected_item.IsOk():
            return

        connection = self.connections_tree_controller.model.ItemToObject(selected_item)
        if not isinstance(connection, Connection):
            return

        expanded_paths = self._capture_expanded_directory_paths()

        cloned_connection = dataclasses.replace(
            connection,
            id=-1,
            name=self._generate_clone_name(connection.name),
        )

        parent = self._repository.find_connection_parent_directory(connection.id)
        self._pending_parent_directory_id = parent.id if parent else None
        self._repository.add_connection(cloned_connection, parent)

        refreshed_connection = self._find_connection_by_id(cloned_connection.id)
        if refreshed_connection is None:
            refreshed_connection = cloned_connection

        CURRENT_CONNECTION(refreshed_connection)
        PENDING_CONNECTION(None)
        wx.CallAfter(self._restore_expanded_directory_paths, expanded_paths)
        wx.CallAfter(self._select_connection_in_tree, refreshed_connection)

    def on_rename(self, event):
        selected_item = self._get_action_item()
        if selected_item is None or not selected_item.IsOk():
            return

        self.connections_tree_controller.edit_item(selected_item)

    def verify_session(self, session: Session):
        started_at = time.perf_counter()

        with Loader.cursor_wait():
            try:
                tls_was_enabled = bool(
                    getattr(session.connection.configuration, "use_tls_enabled", False)
                )

                logger.debug(
                    "Verifying session connection=%s engine=%s host=%s port=%s user=%s use_tls_enabled=%s",
                    session.connection.name,
                    session.connection.engine,
                    getattr(session.connection.configuration, "hostname", None),
                    getattr(session.connection.configuration, "port", None),
                    getattr(session.connection.configuration, "username", None),
                    tls_was_enabled,
                )
                session.connect(connect_timeout=10)

                tls_is_enabled = bool(
                    getattr(session.connection.configuration, "use_tls_enabled", False)
                )
                if not tls_was_enabled and tls_is_enabled:
                    self.connections_model.use_tls_enabled(True)

                    if not session.connection.is_new:
                        self._repository.save_connection(session.connection)

                    wx.MessageDialog(
                        None,
                        message=_(
                            "This connection cannot work without TLS. TLS has been enabled automatically."
                        ),
                        caption=_("Connection"),
                        style=wx.OK | wx.ICON_INFORMATION,
                    ).ShowModal()

                duration_ms = int((time.perf_counter() - started_at) * 1000)
                self._record_connection_attempt(
                    session.connection,
                    success=True,
                    duration_ms=duration_ms,
                )
                self._sync_statistics_to_model(session.connection)
            except Exception as ex:
                duration_ms = int((time.perf_counter() - started_at) * 1000)
                self._record_connection_attempt(
                    session.connection,
                    success=False,
                    duration_ms=duration_ms,
                    failure_reason=str(ex),
                )
                self._sync_statistics_to_model(session.connection)

                wx.MessageDialog(
                    None,
                    message=_(f"Connection error:\n{str(ex)}"),
                    caption=_("Connection error"),
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ).ShowModal()
                raise ConnectionError(ex)

    def on_connect(self, event):
        if PENDING_CONNECTION() and not self.on_save(event):
            return

        connection = CURRENT_CONNECTION()

        session = Session(connection)

        try:
            self.verify_session(session)
        except ConnectionError as ex:
            logger.info(ex)
        except Exception as ex:
            logger.error(ex, exc_info=True)
        else:
            self.do_open_session(session)

    def on_delete_connection(self, connection: Connection):
        dialog = wx.MessageDialog(
            None,
            message=_(f"Do you want to delete the connection '{connection.name}'?"),
            caption=_("Confirm delete"),
            style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
        )

        if dialog.ShowModal() == wx.ID_YES:
            PENDING_CONNECTION(None)
            CURRENT_CONNECTION(None)
            self._repository.delete_connection(connection)

        dialog.Destroy()

    def on_delete_directory(self, directory: ConnectionDirectory):
        dialog = wx.MessageDialog(
            None,
            message=_(f"Do you want to delete the directory '{directory.name}'?"),
            caption=_("Confirm delete"),
            style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
        )

        if dialog.ShowModal() == wx.ID_YES:
            PENDING_CONNECTION(None)
            CURRENT_CONNECTION(None)
            CURRENT_DIRECTORY(None)
            self._repository.delete_directory(directory)

        dialog.Destroy()

    def on_delete(self, *args):
        selected_item = self._get_action_item()
        if selected_item is None or not selected_item.IsOk():
            return

        expanded_paths = self._capture_expanded_directory_paths()
        obj = self.connections_tree_controller.model.ItemToObject(selected_item)

        if isinstance(obj, Connection):
            self.on_delete_connection(obj)
        elif isinstance(obj, ConnectionDirectory):
            self.on_delete_directory(obj)

        wx.CallAfter(self._restore_expanded_directory_paths, expanded_paths)

    def on_exit(self, event):
        if not self._app.main_frame:
            self._app.do_exit(event)
        else:
            self.Hide()

        event.Skip()
