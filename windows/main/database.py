from typing import Optional

import wx
import wx.dataview

from helpers import bytes_to_human
from helpers.dataview import AbstractBaseDataModel, BaseDataViewModel, BaseDataViewIndexListModel, ColumnField
from structures.engines.database import SQLTable, SQLDatabase
from windows.main import CURRENT_SESSION, CURRENT_DATABASE, CURRENT_TABLE


class ModelDatabaseTable(BaseDataViewIndexListModel):
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

        return self.MAP_COLUMN_FIELDS[col](table)


class ListDatabaseTable:
    def __init__(self, list_ctrl_database_tables: wx.dataview.DataViewCtrl):
        self.list_ctrl_database_tables = list_ctrl_database_tables
        self.list_ctrl_database_tables.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self._on_item_activated)

        self.model = ModelDatabaseTable(7)
        self.list_ctrl_database_tables.AssociateModel(self.model)

        CURRENT_DATABASE.subscribe(self._load_database)

    def _load_database(self, database: SQLDatabase):
        if database:
            self.model.set_observable(database.tables)

    def _on_item_activated(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()
        if not item.IsOk():
            return

        if table := self.model.get_data_by_item(item):
            CURRENT_TABLE.set_value(table.copy())
