import wx

from typing import Type, Iterator, Union, List

from sqlalchemy import Table

from icons import ImageList, IconList

from models.session import Session, SessionEngine
from models.database import Database

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION


class TreeSessionsController:
    def __init__(self, tree_ctrl_sessions: wx.TreeCtrl):
        self.app = wx.GetApp()

        self.tree_ctrl_sessions = tree_ctrl_sessions
        self.tree_ctrl_sessions.SetImageList(ImageList)

        self.tree_ctrl_sessions_root = self.tree_ctrl_sessions.AddRoot("sessions")

        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_select_item)

        CURRENT_DATABASE.subscribe(self.on_select_database)

    def load_child(self, parent, children: Union[Iterator[Database], List[Table]]):
        self.tree_ctrl_sessions.DeleteChildren(parent)

        for child in children:
            item = self.tree_ctrl_sessions.AppendItem(parent=parent, text=child.name, data=child)
            child.control = item

            if type(child) is Database:
                self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_DATABASE, wx.TreeItemIcon_Normal)
            elif type(child) is Table:
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

        session_tree_item = self.tree_ctrl_sessions.AppendItem(self.tree_ctrl_sessions_root, text=session.name, data=session)

        self.tree_ctrl_sessions.SetItemImage(session_tree_item, icon, wx.TreeItemIcon_Normal)

        self.tree_ctrl_sessions.SelectItem(session_tree_item)

        self.load_child(session_tree_item, session.statement.get_databases())

    def on_select_database(self, database: Database):
        with self.app.cursor_wait():
            if database is not None:
                self.load_child(
                    parent=database.control,
                    children=list(database.tables)
                )

    def on_select_item(self, event: wx.TreeEvent):
        item = event.GetItem()
        data = self.tree_ctrl_sessions.GetItemData(item)
        parent = self.tree_ctrl_sessions.GetItemParent(item)

        if isinstance(data, Session):
            CURRENT_SESSION.set_value(data)
            CURRENT_DATABASE.set_value(None)
            CURRENT_TABLE.set_value(None)

        if isinstance(data, Database):
            CURRENT_SESSION.set_value(self.tree_ctrl_sessions.GetItemData(parent))
            CURRENT_DATABASE.set_value(data)
            CURRENT_TABLE.set_value(None)

        elif isinstance(data, Table):
            CURRENT_SESSION.set_value(self.tree_ctrl_sessions.GetItemData(self.tree_ctrl_sessions.GetItemParent(parent)))
            CURRENT_DATABASE.set_value(self.tree_ctrl_sessions.GetItemData(parent))
            CURRENT_TABLE.set_value(data)

    def find_by_data(self, **filters):
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
