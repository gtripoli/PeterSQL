from typing import List

import wx
import wx.dataview

from helpers.dataview import BaseDataViewListModel, ColumnField

from structures.helpers import merge_original_current

from windows.main import CURRENT_TABLE, CURRENT_INDEX
from windows.main.column import NEW_TABLE

from structures.engines.database import SQLTable, SQLIndex


class TableIndexModel(BaseDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", lambda i, x: wx.dataview.DataViewIconText(i.name, i.type.bitmap)),
        1: ColumnField("expression", lambda i, x: ", ".join(i.columns)),
        2: ColumnField("condition"),
    }

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        org_ix: SQLIndex = self.get_data_by_row(row)
        new_ix: SQLIndex = org_ix.copy()

        if col == 0:
            new_ix.name = value.Text
        elif col == 1:
            if new_ix.expression:
                new_ix.expression = list(map(str.strip, value.split(", ")))
            else:
                new_ix.columns = value.split(", ")
        elif col == 2:
            new_ix.condition = value if value else None

        if new_ix != org_ix:
            self.set_data_by_row(row, new_ix)
            self.ValueChanged(self.GetItem(row), col)

        return True


class TableIndexController:
    def __init__(self, list_ctrl_index: wx.dataview.DataViewCtrl):
        self.list_ctrl_index = list_ctrl_index

        self.list_ctrl_index.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_index.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        self.model = TableIndexModel(3)
        self.list_ctrl_index.AssociateModel(self.model)

        CURRENT_TABLE.subscribe(self._load_table)
        NEW_TABLE.subscribe(self._load_table)

    def _load_table(self, table : SQLTable):
        self.model.clear()
        if table := NEW_TABLE.get_value() or CURRENT_TABLE.get_value():
            self.model.set_observable(table.indexes)

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            CURRENT_INDEX.set_value(None)

        else:
            row = self.model.GetRow(item)
            index = self.model.data[row]
            CURRENT_INDEX.set_value(index)

        event.Skip()

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_indexes: List[SQLIndex] = self.model.data

        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
        original_indexes: List[SQLIndex] = list(table.indexes)

        map_indexes = merge_original_current(original_indexes, current_indexes)

        if not all([o == c for o, c in map_indexes]):
            table.indexes.set_value(current_indexes)

            NEW_TABLE.set_value(table)

        event.Skip()

    def on_index_delete(self):
        selected = self.list_ctrl_index.GetSelection()
        if not selected.IsOk():
            return

        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        row = self.model.GetRow(selected)
        index = self.model.get_data_by_row(row)

        if index in table.indexes:
            table.indexes.remove(index)

        NEW_TABLE.set_value(table)

    def on_index_clear(self):
        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        self.model.clear()

        table.indexes.clear()

        NEW_TABLE.set_value(table)
