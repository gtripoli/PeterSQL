from typing import Optional

import wx
import wx.dataview

from gettext import gettext as _

from helpers import bytes_to_human
from helpers.dataview import BaseDataViewListModel, ColumnField

from structures.engines.database import SQLTable, SQLDatabase

from windows.main import CURRENT_DATABASE, CURRENT_TABLE, CURRENT_SESSION


# SELECTED_TABLE: Observable[SQLTable] = Observable()

class ModelDatabaseTable(BaseDataViewListModel):
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


class ListDatabaseTable:
    _app = wx.GetApp()

    def __init__(self, list_ctrl_database_tables: wx.dataview.DataViewCtrl):
        self.list_ctrl_database_tables = list_ctrl_database_tables
        self.list_ctrl_database_tables.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)
        self.list_ctrl_database_tables.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)

        self.model = ModelDatabaseTable(7)
        self.list_ctrl_database_tables.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._select_table)

    def _load_database(self, database: SQLDatabase):
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
        if table:
            database = CURRENT_DATABASE.get_value()
            if index := database.tables.index(table):
                self.list_ctrl_database_tables.Select(self.model.GetItem(index))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if table := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(table.copy())

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if table := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(table.copy())
