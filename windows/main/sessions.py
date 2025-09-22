import wx

from typing import Iterator, Union, List

from helpers.observables import Loader
from icons import ImageList, IconList

from models.session import Session, SessionEngine
from models.structures.database import SQLDatabase, SQLTable

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION


class TreeSessionsController:
    def __init__(self, tree_ctrl_sessions: wx.TreeCtrl):
        self.app = wx.GetApp()

        self.tree_ctrl_sessions = tree_ctrl_sessions
        self.tree_ctrl_sessions.SetImageList(ImageList)

        self.tree_ctrl_sessions_root = self.tree_ctrl_sessions.AddRoot("sessions")

        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_select_item)

    def load_child(self, parent: wx.TreeItemId, childrens: Union[Iterator[SQLDatabase], List[SQLTable]]):
        with Loader.cursor_wait():
            print("Load children", childrens)
            self.tree_ctrl_sessions.DeleteChildren(parent)

            for children in childrens:
                item = self.tree_ctrl_sessions.AppendItem(parent=parent, text=children.name, data=children)
                children.control = item

                if type(children) is SQLDatabase:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_DATABASE, wx.TreeItemIcon_Normal)
                elif type(children) is SQLTable:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_TABLE, wx.TreeItemIcon_Normal)

            self.tree_ctrl_sessions.Expand(parent)

    def append_session(self, session: Session):
        icon = IconList.NOT_FOUND
        if session.engine == SessionEngine.MYSQL:
            icon = IconList.ENGINE_MYSQL
        elif session.engine == SessionEngine.MARIADB:
            icon = IconList.ENGINE_MARIADB
        elif session.engine == SessionEngine.SQLITE:
            icon = IconList.ENGINE_SQLITE
        elif session.engine == SessionEngine.POSTGRESQL:
            icon = IconList.ENGINE_POSTGRESQL

        session_tree_item = self.tree_ctrl_sessions.AppendItem(self.tree_ctrl_sessions_root, text=session.name, data=session)

        self.tree_ctrl_sessions.SetItemImage(session_tree_item, icon, wx.TreeItemIcon_Normal)

        self.tree_ctrl_sessions.SelectItem(session_tree_item)

        self.load_child(session_tree_item, session.statement.get_databases())

    def on_select_item(self, event: wx.TreeEvent):
        item = event.GetItem()
        data = self.tree_ctrl_sessions.GetItemData(item)
        parent = self.tree_ctrl_sessions.GetItemParent(item)

        if isinstance(data, Session):
            CURRENT_SESSION.set_value(data)
            CURRENT_DATABASE.set_value(None)
            CURRENT_TABLE.set_value(None)

        if isinstance(data, SQLDatabase):
            session = self.tree_ctrl_sessions.GetItemData(parent)
            CURRENT_SESSION.set_value(session)

            database = data
            CURRENT_DATABASE.set_value(database)

            CURRENT_TABLE.set_value(None)

            self.load_child(data.control, childrens=session.statement.get_tables(database=database))

        elif isinstance(data, SQLTable):
            CURRENT_SESSION.set_value(self.tree_ctrl_sessions.GetItemData(self.tree_ctrl_sessions.GetItemParent(parent)))
            CURRENT_DATABASE.set_value(self.tree_ctrl_sessions.GetItemData(parent))
            CURRENT_TABLE.set_value(data)

    def find_by_data(self, **filters) -> wx.TreeItemId:
        def _matches(data):
            return all(getattr(data, key, None) == value for key, value in filters.items())

        def _search(item):
            if not item.IsOk():
                return None

            data = self.tree_ctrl_sessions.GetItemData(item)
            if data is not None and _matches(data):
                return item

            child, cookie = self.tree_ctrl_sessions.GetFirstChild(item)
            while child.IsOk():
                found = _search(child)
                if found:
                    return found
                child, cookie = self.tree_ctrl_sessions.GetNextChild(item, cookie)

            return None

        return _search(self.tree_ctrl_sessions_root)
