from typing import List

import wx
import wx.dataview

from icons import BitmapList

from windows.main import CURRENT_TABLE, CURRENT_FOREIGN_KEY
from windows.main.table import NEW_TABLE

from models.structures.database import SQLForeignKey, SQLTable


class TableForeignKeyModel(wx.dataview.DataViewIndexListModel):
    def __init__(self):
        super().__init__(0)
        self.data: List[SQLForeignKey] = []

    def GetCount(self):
        return len(self.data)

    def GetColumnCount(self):
        return 6

    def GetColumnType(self, col):
        return "string"

    def GetValueByRow(self, row, col):
        if row >= len(self.data):
            return ""

        fk = self.data[row]

        if col == 0:
            return wx.dataview.DataViewIconText(fk.name, BitmapList.KEY_FOREIGN)
        elif col == 1:
            return ", ".join(fk.columns)
        elif col == 2:
            return fk.reference_table
        elif col == 3:
            return ", ".join(fk.reference_columns)
        elif col == 4:
            return fk.on_update
        elif col == 5:
            return fk.on_delete

        return ""

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        fk = self.data[row]

        if col == 0:
            fk.name = value
        elif col == 1:
            fk.columns = [c.strip() for c in value.split(", ") if c.strip()]
        elif col == 2:
            fk.reference_table = value
        elif col == 3:
            fk.reference_columns = [c.strip() for c in value.split(", ") if c.strip()]
        elif col == 4:
            fk.on_update = value
        elif col == 5:
            fk.on_delete = value

        if fk.name == "" and len(fk.columns) > 0 and fk.reference_table != "" and len(fk.reference_columns) > 0:
            fk.name = f"fk_{CURRENT_TABLE.get_value().name}_{'_'.join(fk.columns)}-{fk.reference_table}_{'_'.join(fk.reference_columns)}"
            self.ValueChanged(self.GetItem(row), 0)

        self.ValueChanged(self.GetItem(row), col)

        return True

    def set_data(self, data: List[SQLForeignKey]):
        self.data = data
        self.Reset(len(data))

    def add_row(self, data: SQLForeignKey) -> wx.dataview.DataViewItem:
        self.data.append(data)
        new_row_index = len(self.data) - 1
        self.RowAppended()
        return self.GetItem(new_row_index)

    def add_empty_row(self) -> wx.dataview.DataViewItem:
        column = SQLForeignKey(
            id=-1,
            name="",
            columns=[],
            reference_table="",
            reference_columns=[],
            on_update="",
            on_delete=""
        )
        return self.add_row(column)

    def clear(self):
        self.data = []
        self.Reset(0)
        self.Cleared()


class TableForeignKeyController:
    def __init__(self, list_ctrl_foreign_key: wx.dataview.DataViewCtrl):
        self.list_ctrl_foreign_key = list_ctrl_foreign_key

        self.model = TableForeignKeyModel()
        self.list_ctrl_foreign_key.AssociateModel(self.model)

        self.list_ctrl_foreign_key.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_foreign_key.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        # Connect callbacks
        self.list_ctrl_foreign_key.on_foreign_key_insert = self.on_foreign_key_insert
        self.list_ctrl_foreign_key.on_foreign_key_delete = self.on_foreign_key_delete

        CURRENT_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.model.clear()

        if table:
            self.model.set_data(list(table.foreign_keys))

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            CURRENT_FOREIGN_KEY.set_value(None)
        else:
            row = self.model.GetRow(item)
            foreign_key = self.model.data[row]
            CURRENT_FOREIGN_KEY.set_value(foreign_key)

        event.Skip()

    def _do_build(self, row: int):
        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        foreign_key: SQLForeignKey = self.model.data[row]

        table.foreign_keys.append(foreign_key, replace_existing=True)

        NEW_TABLE.set_value(table)

    def _do_edit(self, item, column_index: int = 1):
        wx.CallAfter(
            self.list_ctrl_foreign_key.EditItem, item, self.list_ctrl_foreign_key.GetColumn(column_index)
        )

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON FOREIGN KEY EDITING DONE", "#" * 10)

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        row = self.model.GetRow(item)

        self._do_build(row)

        event.Skip()

    def on_foreign_key_insert(self):
        item = self.model.add_empty_row()
        self.list_ctrl_foreign_key.Select(item)

        self._do_edit(item, 1)

    def on_foreign_key_delete(self):
        selected = self.list_ctrl_foreign_key.GetSelection()
        if not selected.IsOk():
            return

        row = self.model.GetRow(selected)
        foreign_key = self.model.data[row]

        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
        if foreign_key in table.foreign_keys:
            table.foreign_keys.remove(foreign_key)

        del self.model.data[row]
        self.model.RowDeleted(row)

        NEW_TABLE.set_value(table)

    def on_foreign_key_clear(self):
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        self.model.clear()

        table.foreign_keys.clear()

        NEW_TABLE.set_value(table)
