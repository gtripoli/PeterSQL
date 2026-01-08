from typing import List

import wx
import wx.dataview

from helpers.dataview import BaseDataViewListModel

from structures.engines import merge_original_current

from windows.main import CURRENT_TABLE, CURRENT_INDEX
from windows.main.column import NEW_TABLE

from structures.engines.database import SQLTable, SQLConstraint


class TableConstraintModel(BaseDataViewListModel):
    def GetValueByRow(self, row, col):
        if row >= len(self.data):
            print(row, len(self.data))
            return ""

        constraint: SQLConstraint = self.get_data_by_row(row)

        if col == 0:
            return wx.dataview.DataViewIconText(constraint.type, wx.NullBitmap)
            return constraint.type
        elif col == 1:
            return constraint.name
        elif col == 2:
            return constraint.expression

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        original = self.get_data_by_row(row)
        new: SQLConstraint = original.copy()

        # if col == 0:
        #     new.name = value.Text
        if col == 1:
            new.name = value
        elif col == 2:
            new.expression = value

        if new != original:
            self.set_data_by_row(row, new)
            self.ValueChanged(self.GetItem(row), col)

        return True


class TableConstraintController:
    def __init__(self, list_ctrl_constraint: wx.dataview.DataViewCtrl):
        self.list_ctrl_constraint = list_ctrl_constraint

        self.list_ctrl_constraint.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_constraint.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        self.model = TableConstraintModel(3)
        self.list_ctrl_constraint.AssociateModel(self.model)

        CURRENT_TABLE.subscribe(self._load_table)
        NEW_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.model.clear()
        if table := NEW_TABLE.get_value() or CURRENT_TABLE.get_value():
            self.model.set_observable(table.constraints)

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            CURRENT_INDEX.set_value(None)

        else:
            row = self.model.GetRow(item)
            constraint = self.model.data[row]
            CURRENT_INDEX.set_value(constraint)

        event.Skip()

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_constraints: List[SQLConstraint] = self.model.data

        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
        original_constraints: List[SQLConstraint] = list(table.constraints)

        map_constraints = merge_original_current(original_constraints, current_constraints)

        if not all([o == c for o, c in map_constraints]):
            table.constraints.set_value(current_constraints)

            NEW_TABLE.set_value(table)

        event.Skip()

    def on_constraint_delete(self):
        selected = self.list_ctrl_constraint.GetSelection()
        if not selected.IsOk():
            return

        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        row = self.model.GetRow(selected)
        constraint = self.model.get_data_by_row(row)

        if constraint in table.constraints:
            table.constraints.remove(constraint)

        NEW_TABLE.set_value(table)

    def on_constraint_clear(self):
        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        self.model.clear()

        table.constraints.clear()

        NEW_TABLE.set_value(table)
