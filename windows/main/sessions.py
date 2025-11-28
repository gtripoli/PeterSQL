import wx
import wx.dataview

from typing import Callable

from icons import BitmapList
from helpers.logger import logger

from engines.session import Session
from engines.structures.database import SQLDatabase, SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION, CURRENT_VIEW, CURRENT_TRIGGER, BaseDataViewModel, SESSIONS, CURRENT_EVENT, CURRENT_FUNCTION, CURRENT_PROCEDURE
from windows.main.table import NEW_TABLE


class SessionListModel(BaseDataViewModel):
    def __init__(self):
        super().__init__(column_count=2)

    def GetColumnType(self, col):
        mapper = {
            0: "string",
            1: "long",
        }
        return mapper[col]

    def GetChildren(self, parent, children):
        if not parent:
            for session in self.data:
                children.append(self.ObjectToItem(session))

            return len(self.data)

        node = self.ItemToObject(parent)
        if isinstance(node, Session):
            databases = node.context.get_databases()
            for database in databases:
                children.append(self.ObjectToItem(database))

            return len(databases)

        if isinstance(node, SQLDatabase):
            length = sum([len(node.tables), len(node.views), len(node.triggers)])

            for table in list(node.tables):
                children.append(self.ObjectToItem(table))
            for view in list(node.views):
                children.append(self.ObjectToItem(view))
            for procedure in list(node.procedures):
                children.append(self.ObjectToItem(procedure))
            for function in list(node.functions):
                children.append(self.ObjectToItem(function))
            for trigger in list(node.triggers):
                children.append(self.ObjectToItem(trigger))
            for event in list(node.events):
                children.append(self.ObjectToItem(event))

            return length

        return 0

    def IsContainer(self, item):
        if not item:
            return True

        node = self.ItemToObject(item)
        if isinstance(node, (Session, SQLDatabase)) :
            return True

        return False

    def GetParent(self, item):
        if not item:
            return wx.dataview.NullDataViewItem

        node = self.ItemToObject(item)
        if isinstance(node, Session):
            return wx.dataview.NullDataViewItem

        elif isinstance(node, SQLDatabase):
            return self.ObjectToItem(node.context.session)
        else:
            return self.ObjectToItem(node.database)

    def GetValue(self, item, col):
        node = self.ItemToObject(item)

        if isinstance(node, Session):
            mapper = {0: wx.dataview.DataViewIconText(node.name, node.context.BITMAP), 1: "", }
        elif isinstance(node, SQLDatabase):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_DATABASE), 1: node.size}
        elif isinstance(node, SQLTable):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_TABLE), 1: int((node.size / node.database.size) * 100)}
        elif isinstance(node, SQLView):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_VIEW), 1: 0}
        elif isinstance(node, SQLProcedure):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_PROCEDURE), 1: 0}
        elif isinstance(node, SQLFunction):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_FUNCTION), 1: 0}
        elif isinstance(node, SQLTrigger):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_TRIGGER), 1: 0}
        elif isinstance(node, SQLEvent):
            mapper = {0: wx.dataview.DataViewIconText(node.name, BitmapList.SYSTEM_EVENT), 1: 0}

        return mapper[col]


class TreeSessionsController:
    on_cancel_table: Callable
    do_cancel_table: Callable

    def __init__(self, tree_ctrl_sessions: wx.dataview.DataViewCtrl):
        self.app = wx.GetApp()

        self.tree_ctrl_sessions = tree_ctrl_sessions

        self.model = SessionListModel()
        self.model.set_observable(SESSIONS)

        self.tree_ctrl_sessions.AssociateModel(self.model)

        self.tree_ctrl_sessions.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.on_selection_changed)

    def on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            event.Veto()
            return

        if NEW_TABLE.get_value() and not self.on_cancel_table(event):
            event.Veto()
            return

        CURRENT_TABLE.set_value(None)
        CURRENT_VIEW.set_value(None)
        CURRENT_TRIGGER.set_value(None)
        CURRENT_PROCEDURE.set_value(None)
        CURRENT_EVENT.set_value(None)
        CURRENT_FUNCTION.set_value(None)

        object = self.model.ItemToObject(item)
        self.tree_ctrl_sessions.Expand(item)

        if isinstance(object, Session):
            if not CURRENT_DATABASE.get_value() or object != CURRENT_SESSION.get_value():
                CURRENT_SESSION.set_value(object)
                CURRENT_DATABASE.set_value(None)

        elif isinstance(object, SQLDatabase):
            if not CURRENT_DATABASE.get_value() or object != CURRENT_DATABASE.get_value():
                database = object
                session = database.context.session
                
                if session != CURRENT_SESSION.get_value():
                    CURRENT_SESSION.set_value(session)

                CURRENT_DATABASE.set_value(database)
                #
                # children = list(database.tables) + list(database.views) + list(database.triggers)
                # self._append_child_rows(session, item, children)

        elif isinstance(object, (SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent)):
            database = object.database
            session = database.context.session
            
            if session != CURRENT_SESSION.get_value() :
                CURRENT_SESSION.set_value(session)
            
            if database != CURRENT_DATABASE.get_value() :
                CURRENT_DATABASE.set_value(database)
            
            if isinstance(object, SQLTable) and (not CURRENT_TABLE.get_value() or object != CURRENT_TABLE.get_value()):
                CURRENT_TABLE.set_value(object.copy())

            elif isinstance(object, SQLView) and (not CURRENT_VIEW.get_value() or object != CURRENT_VIEW.get_value()):
                CURRENT_VIEW.set_value(object.copy())

            elif isinstance(object, SQLTrigger) and (not CURRENT_TRIGGER.get_value() or object != CURRENT_TRIGGER.get_value()):
                CURRENT_TRIGGER.set_value(object.copy())

            elif isinstance(object, SQLProcedure) and (not CURRENT_PROCEDURE.get_value() or object != CURRENT_PROCEDURE.get_value()):
                CURRENT_TRIGGER.set_value(object.copy())

            elif isinstance(object, SQLFunction) and (not CURRENT_FUNCTION.get_value() or object != CURRENT_FUNCTION.get_value()):
                CURRENT_TRIGGER.set_value(object.copy())

            elif isinstance(object, SQLEvent) and (not CURRENT_EVENT.get_value() or object != CURRENT_EVENT.get_value()):
                CURRENT_TRIGGER.set_value(object.copy())
