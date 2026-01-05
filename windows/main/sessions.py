from typing import Callable, List

import wx
import wx.lib.agw.hypertreelist

from gettext import gettext as _

from helpers import bytes_to_human
from icons import IconList, ImageList
from helpers.observables import Loader, CallbackEvent

from structures.session import Session
from structures.engines.database import SQLDatabase, SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION, CURRENT_VIEW, CURRENT_TRIGGER, SESSIONS, CURRENT_EVENT, CURRENT_FUNCTION, CURRENT_PROCEDURE
from windows.main.table import NEW_TABLE


class GaugeWithLabel(wx.Panel):
    def __init__(self, parent, max_range=100, size=(100, 20)):
        super().__init__(parent, size=size)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.gauge = wx.Gauge(self, range=max_range, size=size)
        self.label = wx.StaticText(self, label="0%", style=wx.ALIGN_CENTER)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.gauge, 1, wx.EXPAND, 5)
        self.sizer.Add(self.label, 0, wx.ALIGN_CENTER | wx.TOP, -size[1])

        self.SetSizer(self.sizer)

        self.label.SetForegroundColour(wx.WHITE)
        font = self.label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label.SetFont(font)

    def SetValue(self, val):
        self.gauge.SetValue(val)
        self.label.SetLabel(f"{val}%")
        self.label.Refresh()


class TreeSessionsController:
    on_cancel_table: Callable
    do_cancel_table: Callable

    def __init__(self, tree_ctrl_sessions: wx.lib.agw.hypertreelist.HyperTreeList):
        self.app = wx.GetApp()

        self.tree_ctrl_sessions = tree_ctrl_sessions

        self.tree_ctrl_sessions.AddColumn("Name", width=200)
        self.tree_ctrl_sessions.AddColumn("Usage", width=100, flag=wx.ALIGN_RIGHT)

        self.tree_ctrl_sessions.SetMainColumn(0)
        self.tree_ctrl_sessions.AssignImageList(ImageList)
        self.tree_ctrl_sessions._main_win.Bind(
            wx.EVT_MOUSE_EVENTS, lambda e: None if e.LeftDown() else e.Skip()
        )

        self.populate_tree()

        SESSIONS.subscribe(self.append_session, CallbackEvent.ON_APPEND)

        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_SEL_CHANGED, self._load_items)
        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_ITEM_EXPANDING, self._load_items)
        self.tree_ctrl_sessions.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._load_items)

    def _load_items(self, event: wx.lib.agw.hypertreelist.TreeEvent):
        with Loader.cursor_wait():
            item = event.GetItem()
            if not item.IsOk():
                event.Skip()
                return

            if NEW_TABLE.get_value() and not self.on_cancel_table(event):
                event.Skip()
                return

            self.reset_current_objects()

            obj = self.tree_ctrl_sessions.GetItemPyData(item)
            if obj is None:
                event.Skip()
                return

            if isinstance(obj, Session):
                self.select_session(obj, event)
            elif isinstance(obj, SQLDatabase):
                self.select_database(obj, item, event)
            elif isinstance(
                    obj,
                    (SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent),
            ):
                self.select_sql_object(obj)

            event.Skip()

    def populate_tree(self):
        self.tree_ctrl_sessions.DeleteAllItems()
        self.root_item = self.tree_ctrl_sessions.AddRoot("")

        for session in SESSIONS.get_value():
            self.append_session(session)

    def append_session(self, session: Session):
        self.root_item = self.tree_ctrl_sessions.GetRootItem()

        session_item = self.tree_ctrl_sessions.AppendItem(self.root_item, session.name, image=getattr(IconList, f"ENGINE_{session.engine.name}"), data=session)
        for database in session.context.get_databases():
            db_item = self.tree_ctrl_sessions.AppendItem(session_item, database.name, image=IconList.SYSTEM_DATABASE, data=database)
            self.tree_ctrl_sessions.SetItemText(db_item, bytes_to_human(database.total_bytes), column=1)
            self.tree_ctrl_sessions.AppendItem(db_item, "Loading...", image=IconList.CLOCK, data=None)

        self.tree_ctrl_sessions.Expand(session_item)
        self.tree_ctrl_sessions.EnsureVisible(session_item)

        self.tree_ctrl_sessions.Layout()

    def load_observables(self, db_item, database: SQLDatabase):
        for observable_name in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            observable = getattr(database, observable_name, None)
            if observable is None:
                continue
            if database != CURRENT_DATABASE.get_value() and not observable.is_loaded:
                continue

            for obj in observable.get_value():
                obj_item = self.tree_ctrl_sessions.AppendItem(db_item, obj.name, image=getattr(IconList, f"SYSTEM_{observable_name[:-1].upper()}", IconList.NOT_FOUND), data=obj)

                if isinstance(obj, SQLTable):
                    percentage = int((obj.total_bytes / database.total_bytes) * 100) if database.total_bytes else 0

                    gauge_panel = GaugeWithLabel(self.tree_ctrl_sessions, max_range=100, size=(self.tree_ctrl_sessions.GetColumnWidth(1) - 20, self.tree_ctrl_sessions.CharHeight))
                    gauge_panel.SetValue(percentage)
                    self.tree_ctrl_sessions.SetItemWindow(obj_item, gauge_panel, column=1)
                else:
                    self.tree_ctrl_sessions.SetItemText(obj_item, "", column=1)

        loading_item, index_item = self.tree_ctrl_sessions.GetFirstChild(db_item)
        if loading_item and loading_item.GetData() is None:
            self.tree_ctrl_sessions.Delete(loading_item)

    def reset_current_objects(self):
        CURRENT_TABLE.set_value(None)
        CURRENT_VIEW.set_value(None)
        CURRENT_TRIGGER.set_value(None)
        CURRENT_PROCEDURE.set_value(None)
        CURRENT_EVENT.set_value(None)
        CURRENT_FUNCTION.set_value(None)

    def select_session(self, session: Session, event):
        if session == CURRENT_SESSION.get_value() and CURRENT_DATABASE.get_value():
            event.Skip()
            return
        CURRENT_SESSION.set_value(session)
        CURRENT_DATABASE.set_value(None)

    def select_database(self, database: SQLDatabase, item, event):
        if database != CURRENT_DATABASE.get_value():
            session = database.context.session
            if session != CURRENT_SESSION.get_value():
                CURRENT_SESSION.set_value(session)
            CURRENT_DATABASE.set_value(database)
            self.load_observables(item, database)

        if not self.tree_ctrl_sessions.IsExpanded(item):
            wx.CallAfter(self.tree_ctrl_sessions.Expand, item)

    def select_sql_object(self, sql_obj):
        database = sql_obj.database
        session = database.context.session

        if session != CURRENT_SESSION.get_value():
            CURRENT_SESSION.set_value(session)

        if database != CURRENT_DATABASE.get_value():
            CURRENT_DATABASE.set_value(database)

        if isinstance(sql_obj, SQLTable):
            if not CURRENT_TABLE.get_value() or sql_obj != CURRENT_TABLE.get_value():
                CURRENT_TABLE.set_value(sql_obj.copy())

        elif isinstance(sql_obj, SQLView):
            if not CURRENT_VIEW.get_value() or sql_obj != CURRENT_VIEW.get_value():
                CURRENT_VIEW.set_value(sql_obj.copy())

        elif isinstance(sql_obj, SQLTrigger):
            if not CURRENT_TRIGGER.get_value() or sql_obj != CURRENT_TRIGGER.get_value():
                CURRENT_TRIGGER.set_value(sql_obj.copy())

        elif isinstance(sql_obj, SQLProcedure):
            if not CURRENT_PROCEDURE.get_value() or sql_obj != CURRENT_PROCEDURE.get_value():
                CURRENT_PROCEDURE.set_value(sql_obj.copy())

        elif isinstance(sql_obj, SQLFunction):
            if not CURRENT_FUNCTION.get_value() or sql_obj != CURRENT_FUNCTION.get_value():
                CURRENT_FUNCTION.set_value(sql_obj.copy())

        elif isinstance(sql_obj, SQLEvent):
            if not CURRENT_EVENT.get_value() or sql_obj != CURRENT_EVENT.get_value():
                CURRENT_EVENT.set_value(sql_obj.copy())
