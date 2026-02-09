from typing import Optional

import wx
import wx.dataview

from helpers.dataview import BaseDataViewListModel, ColumnField

from structures.helpers import merge_original_current
from structures.engines.database import SQLCheck, SQLTable

from windows.main import CURRENT_INDEX, CURRENT_TABLE
from windows.main.column import NEW_TABLE


class TableCheckModel(BaseDataViewListModel):
    MAP_COLUMN_FIELDS = {
        0: ColumnField("name", lambda s, x: wx.dataview.DataViewIconText(s.name or "", wx.NullBitmap)),
        1: ColumnField("expression"),
    }

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        original = self.get_data_by_row(row)
        new: SQLCheck = original.copy()

        if col == 0:
            new.name = value
        elif col == 1:
            new.expression = value

        if new != original:
            self.set_data_by_row(row, new)
            self.ValueChanged(self.GetItem(row), col)

        return True


class TableCheckController:
    def __init__(self, list_ctrl_constraint: wx.dataview.DataViewCtrl):
        self.list_ctrl_constraint = list_ctrl_constraint

        self.list_ctrl_constraint.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_constraint.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        self.model = TableCheckModel(3)
        self.list_ctrl_constraint.AssociateModel(self.model)

        CURRENT_TABLE.subscribe(self._load_table)
        NEW_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.model.clear()
        if table := NEW_TABLE.get_value() or CURRENT_TABLE.get_value():
            self.model.set_observable(table.checks)

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

        current_checks: list[SQLCheck] = self.model.data

        table: SQLTable = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
        original_checks: list[SQLCheck] = list(table.checks)

        map_checks = merge_original_current(original_checks, current_checks)

        if not all([o == c for o, c in map_checks]):
            table.checks.set_value(current_checks)

            NEW_TABLE.set_value(table)

        event.Skip()

    def on_constraint_delete(self, event: Optional[wx.Event] = None) -> None:
        if self._do_constraint_delete() and event is not None:
            event.Skip()

    def on_constraint_clear(self, event: Optional[wx.Event] = None) -> None:
        if self._do_constraint_clear() and event is not None:
            event.Skip()

    def _do_constraint_delete(self) -> bool:
        selected = self.list_ctrl_constraint.GetSelection()
        if not selected.IsOk():
            return False

        if (table := self._active_table()) is None:
            return False

        row = self.model.GetRow(selected)
        constraint = self.model.get_data_by_row(row)

        if constraint in table.checks:
            table.checks.remove(constraint)
            NEW_TABLE.set_value(table)
            return True
        return False

    def _do_constraint_clear(self) -> bool:
        if (table := self._active_table()) is None:
            return False

        self.model.clear()
        table.checks.clear()
        NEW_TABLE.set_value(table)
        return True

    def _active_table(self) -> Optional[SQLTable]:
        return NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
