import wx
import wx.dataview

from windows.main import CURRENT_TABLE, CURRENT_INDEX, BaseDataViewIndexListModel
from windows.main.column import NEW_TABLE

from engines.structures.database import SQLTable, SQLIndex


class TableIndexModel(BaseDataViewIndexListModel):
    def GetValueByRow(self, row, col):
        if row >= len(self.data):
            print(row, len(self.data))
            return ""

        index: SQLIndex = self.get_data_by_row(row)

        if col == 0:
            return wx.dataview.DataViewIconText(index.name, index.type.bitmap)
        elif col == 1:
            if index.expression:
                return ", ".join(index.expression)
            else:
                return ", ".join(index.columns)
        elif col == 2:
            return index.condition if index.condition else ""

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        index: SQLIndex = self.get_data_by_row(row)

        if col == 0:
            index.name = value.Text
        elif col == 1:
            if index.expression:
                index.expression = list(map(str.strip, value.split(", ")))
            else:
                index.columns = value.split(", ")
        elif col == 2:
            index.condition = value if value else None

        return True

class TableIndexController:
    def __init__(self, list_ctrl_index: wx.dataview.DataViewCtrl):
        self.list_ctrl_index = list_ctrl_index

        self.list_ctrl_index.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_index.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        self.model = TableIndexModel(3)
        self.list_ctrl_index.AssociateModel(self.model)

        CURRENT_TABLE.subscribe(self._load_table)

    def _load_table(self, table):
        self.model.clear()
        if table is not None:
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
        print("#" * 10, "ON INDEX EDITING DONE", "#" * 10)

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        row = self.model.GetRow(item)

        self._do_build(row)

        event.Skip()

    def _do_build(self, row: int):
        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        index: SQLIndex = self.model.get_data_by_row(row)

        table.indexes.append(index, replace_existing=True)

        NEW_TABLE.set_value(table)

    # def on_index_insert(self):
    #     item = self.model.add_empty_row()
    #     self.list_ctrl_foreign_key.Select(item)
    #
    #     self._do_edit(item, 1)

    def on_index_delete(self):
        selected = self.list_ctrl_index.GetSelection()
        if not selected.IsOk():
            return

        row = self.model.GetRow(selected)
        index = self.model.get_data_by_row(row)

        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
        if index in table.indexes:
            table.indexes.remove(index)

        # del self.model.data[row]
        # self.model.RowDeleted(row)

        NEW_TABLE.set_value(table)

    def on_index_clear(self):
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        self.model.clear()

        table.indexes = []

        NEW_TABLE.set_value(table)
