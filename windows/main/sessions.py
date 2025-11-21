import wx

from typing import Iterator, Union, List, Callable

from helpers.observables import Loader
from icons import ImageList, IconList

from engines.session import Session, SessionEngine
from engines.structures.database import SQLDatabase, SQLTable, SQLView, SQLTrigger

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION, CURRENT_VIEW, CURRENT_TRIGGER
from windows.main.table import NEW_TABLE


class TreeSessionsController:
    on_cancel_table: Callable
    do_cancel_table: Callable

    def __init__(self, tree_ctrl_sessions: wx.TreeCtrl):
        self.app = wx.GetApp()

        self.tree_ctrl_sessions = tree_ctrl_sessions
        self.tree_ctrl_sessions.SetImageList(ImageList)

        self.tree_ctrl_sessions_root = self.tree_ctrl_sessions.AddRoot("sessions")

        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_select_item)

    def load_child(self, parent: wx.TreeItemId, childrens: Union[Iterator[SQLDatabase], List[SQLTable]]):
        with Loader.cursor_wait():
            self.tree_ctrl_sessions.DeleteChildren(parent)

            for children in childrens:
                item = self.tree_ctrl_sessions.AppendItem(parent=parent, text=children.name, data=children)
                children.control = item

                if type(children) is SQLDatabase:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_DATABASE, wx.TreeItemIcon_Normal)
                elif type(children) is SQLTable:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_TABLE, wx.TreeItemIcon_Normal)
                elif type(children) is SQLView:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_VIEW, wx.TreeItemIcon_Normal)
                elif type(children) is SQLTrigger:
                    self.tree_ctrl_sessions.SetItemImage(item, IconList.SYSTEM_TRIGGER, wx.TreeItemIcon_Normal)

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

        self.load_child(session_tree_item, session.context.get_databases())

    def on_select_item(self, event: wx.TreeEvent):
        item = event.GetItem()
        data = self.tree_ctrl_sessions.GetItemData(item)
        parent = self.tree_ctrl_sessions.GetItemParent(item)

        if NEW_TABLE.get_value() and not self.on_cancel_table(event):
            event.Veto()
            return

        CURRENT_TABLE.set_value(None)
        CURRENT_VIEW.set_value(None)
        CURRENT_TRIGGER.set_value(None)

        if isinstance(data, Session) and (not CURRENT_DATABASE.get_value() or data.id != CURRENT_SESSION.get_value().id):
            # if CURRENT_SESSION.get_value() and data != CURRENT_SESSION.get_value() :
            CURRENT_SESSION.set_value(data)

            CURRENT_DATABASE.set_value(None)

        elif isinstance(data, SQLDatabase) and (not CURRENT_DATABASE.get_value() or data.id != CURRENT_DATABASE.get_value().id):
            session = self.tree_ctrl_sessions.GetItemData(parent)
            database = data

            if session.id != CURRENT_SESSION.get_value().id:
                CURRENT_SESSION.set_value(session)

            CURRENT_DATABASE.set_value(database)

            self.load_child(data.control, childrens=list(database.tables) + list(database.views) + list(database.triggers))

        else:
            session = self.tree_ctrl_sessions.GetItemData(self.tree_ctrl_sessions.GetItemParent(parent))
            if session.id != CURRENT_SESSION.get_value().id:
                CURRENT_SESSION.set_value(session)

            database = self.tree_ctrl_sessions.GetItemData(parent)
            if database.id != CURRENT_DATABASE.get_value().id:
                CURRENT_DATABASE.set_value(database)

            if isinstance(data, SQLTable) and (not CURRENT_TABLE.get_value() or data.id != CURRENT_TABLE.get_value().id):
                CURRENT_TABLE.set_value(data.copy())

            elif isinstance(data, SQLView) and (not CURRENT_VIEW.get_value() or data.id != CURRENT_VIEW.get_value().id):
                CURRENT_VIEW.set_value(data.copy())

            if isinstance(data, SQLTrigger) and not (CURRENT_TRIGGER.get_value() or data.id != CURRENT_TRIGGER.get_value().id):
                CURRENT_TRIGGER.set_value(data.copy())

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
