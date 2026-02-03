from typing import Optional
from gettext import gettext as _

import wx

from helpers.logger import logger
from helpers.loader import Loader

from structures.connection import Connection, ConnectionEngine

from windows import ConnectionsDialog
from windows.main import CONNECTIONS_LIST

from windows.connections import CURRENT_CONNECTION, PENDING_CONNECTION, ConnectionDirectory, CURRENT_DIRECTORY
from windows.connections.model import ConnectionModel
from windows.connections.controller import ConnectionsTreeController
from windows.connections.repository import ConnectionsRepository


class ConnectionsManager(ConnectionsDialog):
    _app = wx.GetApp()
    _repository = ConnectionsRepository()

    def __init__(self, parent):
        super().__init__(parent)
        self.engine.SetItems([e.name for e in ConnectionEngine.get_all()])

        self.connections_tree_controller = ConnectionsTreeController(self.connections_tree_ctrl, self._repository)
        self.connections_tree_controller.on_item_activated = lambda connection: self.on_open(None)

        self.connections_model = ConnectionModel()
        self.connections_model.bind_controls(
            name=self.name,
            engine=self.engine,
            hostname=self.hostname, port=self.port,
            username=self.username, password=self.password,
            filename=self.filename,
            comments=self.comments,
            ssh_tunnel_enabled=self.ssh_tunnel_enabled, ssh_tunnel_executable=self.ssh_tunnel_executable,
            ssh_tunnel_hostname=self.ssh_tunnel_hostname, ssh_tunnel_port=self.ssh_tunnel_port,
            ssh_tunnel_username=self.ssh_tunnel_username, ssh_tunnel_password=self.ssh_tunnel_password,
            ssh_tunnel_local_port=self.ssh_tunnel_local_port,
        )

        self.connections_model.engine.subscribe(self._on_change_engine)
        self.connections_model.ssh_tunnel_enabled.subscribe(self._on_change_ssh_tunnel)

        self._setup_event_handlers()

    def _on_current_directory(self, directory: Optional[ConnectionDirectory]):
        self.btn_delete.Enable(bool(directory))
        self.btn_create_directory.Enable(not bool(directory))

    def _on_current_connection(self, connection: Optional[Connection]):
        self.btn_open.Enable(bool(connection and connection.is_valid))
        self.btn_delete.Enable(bool(connection))

    def _on_pending_connection(self, connection: Connection):
        item = self.connections_tree_controller.model.ObjectToItem(connection)
        if item.IsOk():
            self.connections_tree_controller.model.ItemChanged(item)

        self.btn_save.Enable(bool(connection and connection.is_valid))
        self.btn_test.Enable(bool(connection and connection.is_valid))
        self.btn_open.Enable(bool(connection and connection.is_valid))

    def _on_connection_activated(self, connection: Connection):
        CURRENT_CONNECTION(connection)
        # self._app.main_frame.show()
        self.on_open(None)

    def _on_change_engine(self, value: str):
        connection_engine = ConnectionEngine.from_name(value)

        self.panel_credentials.Show(connection_engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.POSTGRESQL])
        self.panel_ssh_tunnel.Show(connection_engine in [ConnectionEngine.MYSQL, ConnectionEngine.MARIADB, ConnectionEngine.POSTGRESQL])

        self.panel_source.Show(connection_engine == ConnectionEngine.SQLITE)

        self.panel_source.GetParent().Layout()

    def _on_change_ssh_tunnel(self, enable: bool):
        self.panel_ssh_tunnel.Show(enable)
        self.panel_ssh_tunnel.Enable(enable)
        self.panel_ssh_tunnel.GetParent().Layout()

    def _on_delete_connection(self, event):
        connection = self.connections_tree_ctrl.get_selected_connection()
        if connection:
            if wx.MessageBox(_(f"Are you sure you want to delete connection '{connection.name}'?"),
                             "Confirm Delete", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) == wx.YES:
                self._repository.delete_item(connection)
                self.connections_tree_ctrl.remove_connection(connection)

    def _on_search_changed(self, event):
        search_text = self.search_connection.GetValue()
        self.connections_tree_controller.do_filter_connections(search_text)

    def _setup_event_handlers(self):
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        self.search_connection.Bind(wx.EVT_TEXT, self._on_search_changed)

        CURRENT_DIRECTORY.subscribe(self._on_current_directory)
        CURRENT_CONNECTION.subscribe(self._on_current_connection)
        PENDING_CONNECTION.subscribe(self._on_pending_connection)

    def do_open_connection(self, event):
        connection = CURRENT_CONNECTION()

        CONNECTIONS_LIST.append(connection)

        if not self.GetParent():
            CURRENT_CONNECTION(connection)
            self._app.open_main_frame()

        self.Hide()

    def on_save(self, *args):
        connection = PENDING_CONNECTION.get_value()
        if not connection:
            return False

        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want save the connection {connection.name}?'),
                                  caption=_("Confirm save"),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() != wx.ID_YES:
            return False

        parent_obj = None
        parent_item = None
        selected_item = self.connections_tree_ctrl.GetSelection()
        if selected_item.IsOk():
            selected_obj = self.connections_tree_controller.model.ItemToObject(selected_item)
            if isinstance(selected_obj, ConnectionDirectory):
                parent_obj = selected_obj
                parent_item = selected_item

        if connection.is_new:
            self._repository.add_connection(connection, parent_obj)
        else:
            self._repository.save_connection(connection)

        PENDING_CONNECTION(None)


        item_new_connection = self.connections_tree_controller.model.ObjectToItem(connection)

        print("item_new_connection",item_new_connection)

        self.connections_tree_ctrl.Select(item_new_connection)

        if parent_item :
            self.connections_tree_ctrl.Expand(parent_item)

        CURRENT_CONNECTION(connection)


        return True

    def on_create_connection(self, event):
        self.connections_manager_model.do_create_connection()

    def on_create_directory(self, event):
        # Get selected directory
        parent = None
        selected_item = self.connections_tree_ctrl.GetSelection()
        if selected_item.IsOk():
            obj = self.connections_tree_controller.model.ItemToObject(selected_item)
            if isinstance(obj, ConnectionDirectory):
                return
        new_dir = ConnectionDirectory(name=_("New directory"))
        self._repository.add_directory(new_dir, parent)
        # Select and edit
        item = self.connections_tree_controller.model.ObjectToItem(new_dir)
        if item.IsOk():
            self.connections_tree_ctrl.Select(item)
            self.connections_tree_ctrl.EditItem(item, self.connections_tree_ctrl.GetColumn(0))
        # Expand parent
        if parent:
            parent_item = self.connections_tree_controller.model.ObjectToItem(parent)
            self.connections_tree_ctrl.Expand(parent_item)

    def verify_connection(self, connection: Connection):
        with Loader.cursor_wait():
            try:
                connection.context.connect(connect_timeout=10)
            except Exception as ex:
                wx.MessageDialog(None,
                                 message=_(f'Connection error:\n{str(ex)}'),
                                 caption=_("Connection error"),
                                 style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR).ShowModal()
                raise ConnectionError(ex)

    def on_open(self, event):
        if PENDING_CONNECTION() and not self.on_save(event):
            return

        connection = CURRENT_CONNECTION()
        if connection:
            try:
                self.verify_connection(connection)
            except ConnectionError as ex:
                logger.info(ex)
            except Exception as ex:
                logger.error(ex, exc_info=True)
            else:
                self.do_open_connection(connection)

    def on_delete_connection(self, connection: Connection):
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the {_("connection")} {connection.name}?'),
                                  caption=_(f"Confirm delete"),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            PENDING_CONNECTION(None)
            CURRENT_CONNECTION(None)
            self._repository.delete_connection(connection)
            self._repository.load()

        dialog.Destroy()

    def on_delete_directory(self, directory: ConnectionDirectory):
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the {_("directory")} {directory.name}?'),
                                  caption=_(f"Confirm delete"),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() == wx.ID_YES:
            PENDING_CONNECTION(None)
            CURRENT_CONNECTION(None)
            self._repository.delete_directory(directory)
            # self._repository.refresh()

        dialog.Destroy()

    def on_delete(self, *args):
        selected_item = self.connections_tree_ctrl.GetSelection()
        if not selected_item.IsOk():
            return

        obj = self.connections_tree_controller.model.ItemToObject(selected_item)

        if isinstance(obj, Connection):
            self.on_delete_connection(obj)
        elif isinstance(obj, ConnectionDirectory):
            self.on_delete_directory(obj)

    def on_exit(self, event):
        if not self._app.main_frame:
            self._app.do_exit(event)
        else:
            self.Hide()

        event.Skip()
