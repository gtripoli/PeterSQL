import dataclasses
import os
from typing import Callable

import wx
import wx.lib.agw.hypertreelist

from icons import IconList

from helpers import bytes_to_human
from helpers.loader import Loader
from helpers.logger import logger
from helpers.observables import CallbackEvent

from structures.session import Session
from structures.connection import Connection
from structures.engines.database import SQLDatabase, SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent

from windows.state import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_CONNECTION, CURRENT_SESSION, CURRENT_VIEW, CURRENT_TRIGGER, SESSIONS_LIST, CURRENT_EVENT, CURRENT_FUNCTION, CURRENT_PROCEDURE, NEW_TABLE


@dataclasses.dataclass
class TreeCategory:
    name: str
    icon: wx.BitmapBundle
    database: SQLDatabase


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
        self.gauge.SetValue(int(val))
        self.label.SetLabel(f"{val:0.1f}%")
        self.label.Refresh()


class TreeExplorerController:
    on_cancel_table: Callable
    do_cancel_table: Callable

    def __init__(self, tree_ctrl_explorer: wx.lib.agw.hypertreelist.HyperTreeList):
        self.app = wx.GetApp()

        self.tree_ctrl_explorer = tree_ctrl_explorer
        self._database_items: dict = {}

        self.tree_ctrl_explorer.AddColumn("Name", width=200)
        self.tree_ctrl_explorer.AddColumn("Usage", width=100, flag=wx.ALIGN_RIGHT)

        self.tree_ctrl_explorer.SetMainColumn(0)
        self.tree_ctrl_explorer.AssignImageList(wx.GetApp().icon_registry_16.imagelist)
        self.tree_ctrl_explorer._main_win.Bind(
            wx.EVT_MOUSE_EVENTS, lambda e: None if e.LeftDown() else e.Skip()
        )

        self.populate_tree()

        # self.tree_ctrl_explorer.Bind(wx.EVT_TREE_SEL_CHANGED, self._load_items)
        self.tree_ctrl_explorer.Bind(wx.EVT_TREE_ITEM_EXPANDING, self._load_items)
        self.tree_ctrl_explorer.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._load_items)

        SESSIONS_LIST.subscribe(self.append_session, CallbackEvent.ON_APPEND)

        # CURRENT_DATABASE.get_value().tables.subscribe(self.load_observables, CallbackEvent.ON_APPEND)
        # CURRENT_DATABASE.get_value().views.subscribe(self.load_observables, CallbackEvent.ON_APPEND)
        # CURRENT_DATABASE.get_value().procedures.subscribe(self.load_observables, CallbackEvent.ON_APPEND)
        # CURRENT_DATABASE.get_value().functions.subscribe(self.load_observables, CallbackEvent.ON_APPEND)
        # CURRENT_DATABASE.get_value().triggers.subscribe(self.load_observables, CallbackEvent.ON_APPEND)
        # CURRENT_DATABASE.get_value().events.subscribe(self.load_observables, CallbackEvent.ON_APPEND)

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

            obj = self.tree_ctrl_explorer.GetItemPyData(item)
            if obj is None:
                event.Skip()
                return

            if isinstance(obj, Session):
                self.select_session(obj, event)
            elif isinstance(obj, SQLDatabase):
                parent_item = self.tree_ctrl_explorer.GetItemParent(item)
                parent_session = self.tree_ctrl_explorer.GetItemPyData(parent_item)
                if isinstance(parent_session, Session):
                    self.select_session(parent_session, event)
                self.select_database(obj, item, event)
            elif isinstance(
                    obj,
                    (SQLTable, SQLView, SQLTrigger, SQLProcedure, SQLFunction, SQLEvent),
            ):
                wx.CallAfter(self.select_sql_object, obj)

            event.Skip()

    def populate_tree(self):
        self._database_items = {}
        self.tree_ctrl_explorer.DeleteAllItems()
        self.root_item = self.tree_ctrl_explorer.AddRoot("")

        for session in SESSIONS_LIST.get_value():
            self.append_session(session)

    def append_session(self, session: Session):
        self.root_item = self.tree_ctrl_explorer.GetRootItem()

        session_item = self.tree_ctrl_explorer.AppendItem(self.root_item, session.name, image=wx.GetApp().icon_registry_16.get_index(getattr(IconList, session.engine.name, IconList.NOT_FOUND)), data=session)
        for database in session.context.databases.get_value():
            db_item = self.tree_ctrl_explorer.AppendItem(session_item, database.name, image=wx.GetApp().icon_registry_16.get_index(IconList.DATABASE), data=database)
            self._database_items[id(database)] = db_item
            self.tree_ctrl_explorer.SetItemText(db_item, bytes_to_human(database.total_bytes), column=1)
            self.tree_ctrl_explorer.AppendItem(db_item, "Loading...", image=wx.GetApp().icon_registry_16.get_index(IconList.CLOCK), data=None)

        self.tree_ctrl_explorer.Expand(session_item)
        self.tree_ctrl_explorer.EnsureVisible(session_item)

        self.tree_ctrl_explorer.Layout()

    def load_observables(self, db_item, database: SQLDatabase):
        for observable_name in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            observable = getattr(database, observable_name, None)

            category_item = self.tree_ctrl_explorer.AppendItem(
                db_item,
                observable_name.capitalize(),
                image=wx.GetApp().icon_registry_16.get_index(getattr(IconList, observable_name[:-1].upper(), IconList.NOT_FOUND)),
                data=None
            )

            if observable is None:
                continue

            if database != CURRENT_DATABASE.get_value() and not observable.is_loaded:
                continue

            objs = observable.get_value()
            if not objs:
                continue

            # wx.CallAfter(self.tree_ctrl_explorer.Expand, category_item)

            for obj in objs:
                obj_item = self.tree_ctrl_explorer.AppendItem(
                    category_item,
                    obj.name,
                    image=wx.GetApp().icon_registry_16.get_index(getattr(IconList, observable_name[:-1].upper(), IconList.NOT_FOUND)),
                    data=obj
                )

                if isinstance(obj, SQLTable):
                    percentage = float((obj.total_bytes / database.total_bytes) * 100) if database.total_bytes else 0

                    gauge_panel = GaugeWithLabel(self.tree_ctrl_explorer, max_range=100, size=(self.tree_ctrl_explorer.GetColumnWidth(1) - 20, self.tree_ctrl_explorer.CharHeight))
                    gauge_panel.SetValue(percentage)
                    self.tree_ctrl_explorer.SetItemWindow(obj_item, gauge_panel, column=1)
                else:
                    self.tree_ctrl_explorer.SetItemText(obj_item, "", column=1)

        loading_item, index_item = self.tree_ctrl_explorer.GetFirstChild(db_item)
        if loading_item and loading_item.GetData() is None:
            self.tree_ctrl_explorer.Delete(loading_item)

    def reset_current_objects(self):
        logger.debug(
            "ui trace: explorer.reset_current_objects before table=%s view=%s trigger=%s",
            getattr(CURRENT_TABLE.get_value(), "name", None) if CURRENT_TABLE.get_value() is not None else None,
            getattr(CURRENT_VIEW.get_value(), "name", None) if CURRENT_VIEW.get_value() is not None else None,
            getattr(CURRENT_TRIGGER.get_value(), "name", None) if CURRENT_TRIGGER.get_value() is not None else None,
        )
        CURRENT_TABLE.set_value(None)
        CURRENT_VIEW.set_value(None)
        CURRENT_TRIGGER.set_value(None)
        CURRENT_PROCEDURE.set_value(None)
        CURRENT_EVENT.set_value(None)
        CURRENT_FUNCTION.set_value(None)
        logger.debug("ui trace: explorer.reset_current_objects after clear")

    def select_session(self, session: Session, event):
        if session == CURRENT_SESSION.get_value() and CURRENT_DATABASE.get_value():
            CURRENT_SESSION.execute_callback(CallbackEvent.AFTER_CHANGE)
            event.Skip()
            return
        CURRENT_SESSION.set_value(session)
        CURRENT_CONNECTION.set_value(session.connection)
        # CURRENT_DATABASE.set_value(None)

    def select_database(self, database: SQLDatabase, item, event):
        if database != CURRENT_DATABASE.get_value():
            session = CURRENT_SESSION.get_value()
            if session and session.connection != CURRENT_CONNECTION.get_value():
                CURRENT_CONNECTION.set_value(session.connection)

            if session and not session.is_connected:
                while wx.MessageDialog(None,
                                   message="not connected").ShowModal() == wx.ID_OK:
                    session.connect()

            self.reset_current_objects()
            CURRENT_DATABASE.set_value(database)
            CURRENT_SESSION.get_value().context.set_database(database)

            self.load_observables(item, database)

        if not self.tree_ctrl_explorer.IsExpanded(item):
            wx.CallAfter(self.tree_ctrl_explorer.Expand, item)

    def select_sql_object(self, sql_obj):
        database = sql_obj.database
        session = CURRENT_SESSION.get_value()

        if session and session.connection != CURRENT_CONNECTION.get_value():
            CURRENT_CONNECTION.set_value(session.connection)

        if database != CURRENT_DATABASE.get_value():
            CURRENT_DATABASE.set_value(database)
            CURRENT_SESSION.get_value().context.set_database(database)

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

    def refresh_current_database(self):
        database = CURRENT_DATABASE.get_value()
        if not database:
            logger.debug("explorer refresh: no current database")
            return

        db_item = self._database_items.get(id(database))
        if db_item is None or not db_item.IsOk():
            logger.debug("explorer refresh: db_item not found for database=%s id=%s keys=%s", database.name, id(database), list(self._database_items.keys()))
            return

        logger.debug("explorer refresh: refreshing database=%s", database.name)
        for observable_name in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            observable = getattr(database, observable_name, None)
            if observable is not None and observable.is_loaded:
                logger.debug("explorer refresh: refreshing observable=%s", observable_name)
                observable.refresh()
            else:
                logger.debug("explorer refresh: skipping observable=%s is_loaded=%s", observable_name, getattr(observable, "is_loaded", None))

        self.tree_ctrl_explorer.DeleteChildren(db_item)
        self._load_observables_for_refresh(db_item, database)
        self.tree_ctrl_explorer.Expand(db_item)
        self.tree_ctrl_explorer.Layout()

    def _load_observables_for_refresh(self, db_item, database: SQLDatabase):
        for observable_name in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            observable = getattr(database, observable_name, None)

            category_item = self.tree_ctrl_explorer.AppendItem(
                db_item,
                observable_name.capitalize(),
                image=wx.GetApp().icon_registry_16.get_index(
                    getattr(IconList, observable_name[:-1].upper(), IconList.NOT_FOUND)
                ),
                data=None
            )

            if observable is None or not observable.is_loaded:
                continue

            objs = observable.get_value()
            if not objs:
                continue

            for obj in objs:
                obj_item = self.tree_ctrl_explorer.AppendItem(
                    category_item,
                    obj.name,
                    image=wx.GetApp().icon_registry_16.get_index(
                        getattr(IconList, observable_name[:-1].upper(), IconList.NOT_FOUND)
                    ),
                    data=obj
                )

                if isinstance(obj, SQLTable):
                    percentage = int((obj.total_bytes / database.total_bytes) * 100) if database.total_bytes else 0
                    self.tree_ctrl_explorer.SetItemText(obj_item, f"{percentage}%", column=1)
                else:
                    self.tree_ctrl_explorer.SetItemText(obj_item, "", column=1)
