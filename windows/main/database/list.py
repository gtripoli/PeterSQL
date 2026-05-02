from typing import Optional

import wx
import wx.dataview

from gettext import gettext as _

from helpers import bytes_to_human
from helpers.dataview import BaseObservableDataViewListModel, ColumnField
from helpers.logger import logger

from structures.engines.database import SQLTable, SQLDatabase, SQLView, SQLProcedure, SQLFunction, SQLTrigger, SQLEvent

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION, CURRENT_VIEW, CURRENT_PROCEDURE, CURRENT_FUNCTION, CURRENT_TRIGGER, CURRENT_EVENT


class ModelDatabaseTable(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("total_rows", str),
        2: ColumnField("total_bytes", bytes_to_human),
        3: ColumnField("created_at"),
        4: ColumnField("updated_at"),
        5: ColumnField("engine", str),
        6: ColumnField("collation_name", str),
        7: ColumnField("comment", str),
    }

    def __init__(self, column_count: Optional[int] = None):
        super().__init__(column_count)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        table: SQLTable = self.get_data_by_row(row)

        return self.MAP_COLUMN_FIELDS[col].get_value(table)

    def Compare(self, item1, item2, col, ascending):
        table1: SQLTable = self.get_data_by_item(item1)
        table2: SQLTable = self.get_data_by_item(item2)

        if col == 1:
            rows1 = int(table1.total_rows)
            rows2 = int(table2.total_rows)
            if rows1 == rows2:
                return 0
            if ascending:
                return -1 if rows1 < rows2 else 1
            return -1 if rows1 > rows2 else 1

        if col == 2:
            size1 = int(table1.total_bytes)
            size2 = int(table2.total_bytes)
            if size1 == size2:
                return 0
            if ascending:
                return -1 if size1 < size2 else 1
            return -1 if size1 > size2 else 1

        value1 = self.MAP_COLUMN_FIELDS[col].get_value(table1)
        value2 = self.MAP_COLUMN_FIELDS[col].get_value(table2)
        if value1 == value2:
            return 0
        if ascending:
            return -1 if value1 < value2 else 1
        return -1 if value1 > value2 else 1


class ListDatabaseTable:
    _app = wx.GetApp()

    def __init__(self, list_ctrl_database_tables: wx.dataview.DataViewCtrl):
        self.list_ctrl_database_tables = list_ctrl_database_tables
        self.list_ctrl_database_tables.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)

        self.model = ModelDatabaseTable(7)
        self.list_ctrl_database_tables.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._select_table)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            logger.debug("ui trace: list._load_database rescheduled to main thread")
            wx.CallAfter(self._load_database, database)
            return

        if not database:
            return

        parent = self._app.GetTopWindow()

        while True:
            try:
                self.model.set_observable(database.tables)
                return

            except Exception as ex:
                if wx.MessageDialog(
                        parent=parent,
                        message=(
                                _("The connection to the database was lost.")
                                + "\n\n"
                                + _("Do you want to reconnect?")
                        ),
                        caption=_("Connection lost"),
                        style=wx.OK | wx.CANCEL | wx.ICON_WARNING,
                ).ShowModal() != wx.ID_OK:
                    return

                try:
                    if session := CURRENT_SESSION.get_value():
                        session.connect()
                except Exception as reconnect_ex:
                    wx.MessageBox(
                        _("Reconnection failed:") + "\n" + str(reconnect_ex),
                        _("Error"),
                        wx.OK | wx.ICON_ERROR,
                        parent=parent,
                    )

    def _select_table(self, table: SQLTable):
        if not wx.IsMainThread():
            logger.debug("ui trace: list._select_table rescheduled to main thread")
            wx.CallAfter(self._select_table, table)
            return

        if table:
            database = CURRENT_DATABASE.get_value()
            if index := database.tables.index(table):
                self.list_ctrl_database_tables.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if table := self.model.get_data_by_item(item):
            CURRENT_VIEW.set_value(None)
            CURRENT_TABLE.set_value(table.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if table := self.model.get_data_by_item(item):
            CURRENT_VIEW.set_value(None)
            CURRENT_TABLE.set_value(table.copy())


def _truncate_statement(value: str) -> str:
    if not value:
        return ""
    value = " ".join(value.split())
    return value[:120] + "..." if len(value) > 120 else value


class ModelDatabaseView(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("statement", _truncate_statement),
    }

    def __init__(self):
        super().__init__(2)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None
        view: SQLView = self.get_data_by_row(row)
        return self.MAP_COLUMN_FIELDS[col].get_value(view)


class ListDatabaseView:
    _app = wx.GetApp()

    def __init__(self, list_ctrl: wx.dataview.DataViewCtrl):
        self.list_ctrl = list_ctrl
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseView()
        self.list_ctrl.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_VIEW.subscribe(self._select_view)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            wx.CallAfter(self._load_database, database)
            return

        if not database:
            return

        try:
            self.model.set_observable(database.views)
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _select_view(self, view: SQLView):
        if not wx.IsMainThread():
            wx.CallAfter(self._select_view, view)
            return

        if not view or view.is_new:
            return

        database = CURRENT_DATABASE.get_value()
        if not database:
            return

        views = database.views.get_value()
        index = next((i for i, v in enumerate(views) if v.id == view.id), None)
        if index is not None:
            self.list_ctrl.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if view := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(view.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if view := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(view.copy())


class ModelDatabaseProcedure(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("parameters", str),
    }

    def __init__(self):
        super().__init__(2)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None
        procedure: SQLProcedure = self.get_data_by_row(row)
        return self.MAP_COLUMN_FIELDS[col].get_value(procedure)


class ListDatabaseProcedure:
    def __init__(self, list_ctrl: wx.dataview.DataViewCtrl):
        self.list_ctrl = list_ctrl
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseProcedure()
        self.list_ctrl.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_PROCEDURE.subscribe(self._select_procedure)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            wx.CallAfter(self._load_database, database)
            return

        if not database:
            return

        if not hasattr(database, "procedures"):
            return

        try:
            self.model.set_observable(database.procedures)
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _select_procedure(self, procedure: SQLProcedure):
        if not wx.IsMainThread():
            wx.CallAfter(self._select_procedure, procedure)
            return

        if not procedure or procedure.is_new:
            return

        database = CURRENT_DATABASE.get_value()
        if not database or not hasattr(database, "procedures"):
            return

        procedures = database.procedures.get_value()
        index = next((i for i, p in enumerate(procedures) if p.id == procedure.id), None)
        if index is not None:
            self.list_ctrl.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if procedure := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_PROCEDURE.set_value(procedure.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if procedure := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_PROCEDURE.set_value(procedure.copy())


class ModelDatabaseFunction(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("statement", _truncate_statement),
    }

    def __init__(self):
        super().__init__(2)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None
        function: SQLFunction = self.get_data_by_row(row)
        return self.MAP_COLUMN_FIELDS[col].get_value(function)


class ListDatabaseFunction:
    def __init__(self, list_ctrl: wx.dataview.DataViewCtrl):
        self.list_ctrl = list_ctrl
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseFunction()
        self.list_ctrl.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_FUNCTION.subscribe(self._select_function)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            wx.CallAfter(self._load_database, database)
            return

        if not database or not hasattr(database, "functions"):
            return

        try:
            self.model.set_observable(database.functions)
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _select_function(self, function: SQLFunction):
        if not wx.IsMainThread():
            wx.CallAfter(self._select_function, function)
            return

        if not function or function.is_new:
            return

        database = CURRENT_DATABASE.get_value()
        if not database or not hasattr(database, "functions"):
            return

        functions = database.functions.get_value()
        index = next((i for i, f in enumerate(functions) if f.id == function.id), None)
        if index is not None:
            self.list_ctrl.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if function := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_FUNCTION.set_value(function.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if function := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_FUNCTION.set_value(function.copy())


class ModelDatabaseTrigger(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("statement", _truncate_statement),
    }

    def __init__(self):
        super().__init__(2)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None
        trigger: SQLTrigger = self.get_data_by_row(row)
        return self.MAP_COLUMN_FIELDS[col].get_value(trigger)


class ListDatabaseTrigger:
    def __init__(self, list_ctrl: wx.dataview.DataViewCtrl):
        self.list_ctrl = list_ctrl
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseTrigger()
        self.list_ctrl.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TRIGGER.subscribe(self._select_trigger)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            wx.CallAfter(self._load_database, database)
            return

        if not database or not hasattr(database, "triggers"):
            return

        try:
            self.model.set_observable(database.triggers)
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _select_trigger(self, trigger: SQLTrigger):
        if not wx.IsMainThread():
            wx.CallAfter(self._select_trigger, trigger)
            return

        if not trigger or trigger.is_new:
            return

        database = CURRENT_DATABASE.get_value()
        if not database or not hasattr(database, "triggers"):
            return

        triggers = database.triggers.get_value()
        index = next((i for i, t in enumerate(triggers) if t.id == trigger.id), None)
        if index is not None:
            self.list_ctrl.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if trigger := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_TRIGGER.set_value(trigger.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if trigger := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_TRIGGER.set_value(trigger.copy())


class ModelDatabaseEvent(BaseObservableDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", str),
        1: ColumnField("statement", _truncate_statement),
    }

    def __init__(self):
        super().__init__(2)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None
        db_event: SQLEvent = self.get_data_by_row(row)
        return self.MAP_COLUMN_FIELDS[col].get_value(db_event)


class ListDatabaseEvent:
    def __init__(self, list_ctrl: wx.dataview.DataViewCtrl):
        self.list_ctrl = list_ctrl
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseEvent()
        self.list_ctrl.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_EVENT.subscribe(self._select_event)

    def _load_database(self, database: SQLDatabase):
        if not wx.IsMainThread():
            wx.CallAfter(self._load_database, database)
            return

        if not database or not hasattr(database, "events"):
            return

        try:
            self.model.set_observable(database.events)
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _select_event(self, event: SQLEvent):
        if not wx.IsMainThread():
            wx.CallAfter(self._select_event, event)
            return

        if not event or event.is_new:
            return

        database = CURRENT_DATABASE.get_value()
        if not database or not hasattr(database, "events"):
            return

        events = database.events.get_value()
        index = next((i for i, e in enumerate(events) if e.id == event.id), None)
        if index is not None:
            self.list_ctrl.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if db_event := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_EVENT.set_value(db_event.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if db_event := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(None)
            CURRENT_VIEW.set_value(None)
            CURRENT_EVENT.set_value(db_event.copy())
