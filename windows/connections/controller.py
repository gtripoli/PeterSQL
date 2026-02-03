from typing import Optional, Any, Callable

import wx
import wx.dataview

from helpers.dataview import BaseDataViewTreeModel

from structures.connection import Connection

from . import CURRENT_CONNECTION, ConnectionDirectory, CURRENT_DIRECTORY
from windows.connections.repository import ConnectionsRepository


class ConnectionsTreeModel(BaseDataViewTreeModel):

    def __init__(self):
        super().__init__(column_count=2)
        self._parent_map = {}

    def GetColumnType(self, col):
        if col == 0:
            return wx.dataview.DataViewIconText

        return "string"

    def GetChildren(self, parent, children):
        if not parent:
            for item in self.data:
                children.append(self.ObjectToItem(item))
        else:
            obj = self.ItemToObject(parent)
            if isinstance(obj, ConnectionDirectory):
                for child in obj.children:
                    children.append(self.ObjectToItem(child))
                    self._parent_map[self.ObjectToItem(child)] = parent

        return len(children)

    def IsContainer(self, item):
        if not item:
            return True

        obj = self.ItemToObject(item)
        return isinstance(obj, ConnectionDirectory)

    def GetParent(self, item):
        return self._parent_map.get(item, wx.dataview.NullDataViewItem)

    def GetValue(self, item, col):
        node = self.ItemToObject(item)

        if isinstance(node, Connection):
            bitmap = node.engine.value.bitmap
            mapper = {0: wx.dataview.DataViewIconText(node.name, wx.GetApp().icon_registry_16.get_bitmap(bitmap) ), 1: ""}
        elif isinstance(node, ConnectionDirectory):
            mapper = {0: wx.dataview.DataViewIconText(node.name), 1: ""}
        else:
            mapper = {}

        return mapper[col]

    def SetValue(self, variant, item, col):
        print("SetValue")
        node = self.ItemToObject(item)
        if isinstance(node, ConnectionDirectory):
            node.name = variant.GetText()
            # self.repository.save_directory(node)

        if isinstance(node, Connection):
            node.name = variant.GetText()
            # self.repository.save_connection(node)

        return True


class ConnectionsTreeController():
    on_selection_chance: Callable[[Optional[Any]], Optional[Any]] = None
    on_item_activated: Callable[[Optional[Any]], Optional[Any]] = None

    def __init__(self, connections_tree_ctrl: wx.dataview.DataViewCtrl, repository: ConnectionsRepository):
        self.connections_tree_ctrl = connections_tree_ctrl
        self.repository = repository

        self.model = ConnectionsTreeModel()
        self.model.set_observable(self.repository.connections)
        self.connections_tree_ctrl.AssociateModel(self.model)

        self.connections_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE, self._on_item_editing_done)
        self.connections_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING, self._on_item_start_editing)

        self.connections_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.connections_tree_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)

        CURRENT_CONNECTION.subscribe(self._on_current_connection)

    def _on_item_editing_done(self, event):
        item = event.GetItem()

        if not item.IsOk:
            return

        obj = self.model.ItemToObject(item)

        if isinstance(obj, ConnectionDirectory):
            self.repository.save_directory(obj)

        elif isinstance(obj, Connection):
            self.repository.save_connection(obj)

    def _on_item_start_editing(self, event):
        item = event.GetItem()

        if not item.IsOk:
            return

        obj = self.model.ItemToObject(item)

        if isinstance(obj, Connection):
            event.Veto()

    def do_filter_connections(self, search_text):
        # self.search_text = search_text
        # self._update_displayed_connections()
        self.repository.connections.filter(lambda x: search_text.lower() in x.name.lower())

    def _on_selection_changed(self, event):
        item = event.GetItem()

        if not item.IsOk():
            return

        CURRENT_DIRECTORY(None)
        CURRENT_CONNECTION(None)

        obj = self.model.ItemToObject(item)

        if isinstance(obj, Connection):
            CURRENT_CONNECTION(obj)

        elif isinstance(obj, ConnectionDirectory):
            CURRENT_DIRECTORY(obj)

        event.Skip()

    def _on_item_activated(self, event):
        item: wx.dataview.DataViewItem = event.GetItem()
        if not item.IsOk():
            return

        obj = self.model.ItemToObject(item)

        if isinstance(obj, ConnectionDirectory):
            if self.connections_tree_ctrl.IsExpanded(item):
                self.connections_tree_ctrl.Collapse(item)
            else:
                self.connections_tree_ctrl.Expand(item)
            return

        elif isinstance(obj, Connection):
            CURRENT_CONNECTION(None)(obj)

            if self.on_item_activated:
                self.on_item_activated(obj)

        event.Skip()

    def _on_current_connection(self, connection: Optional[Connection]):
        if connection:
            item = self.model.ObjectToItem(connection)
            if not self.connections_tree_ctrl.IsSelected(item) :
                print("select")
                self.connections_tree_ctrl.Select(item)
                self.connections_tree_ctrl.EnsureVisible(item)