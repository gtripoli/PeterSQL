from typing import List

import wx
import wx.dataview

from icons import BitmapList

from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel
from helpers.observables import Loader

from structures.helpers import merge_original_current

from windows import TableForeignKeysDataViewCtrl
from windows.main import CURRENT_TABLE, CURRENT_FOREIGN_KEY, CURRENT_SESSION
from windows.main.table import NEW_TABLE

from structures.engines.database import SQLForeignKey, SQLTable


class TableForeignKeyModel(BaseDataViewListModel):

    def GetValueByRow(self, row, col):
        if row >= len(self.data):
            return ""

        fk = self.get_data_by_row(row)

        if col == 0:
            return wx.dataview.DataViewIconText(fk.name, BitmapList.KEY_FOREIGN)
        elif col == 1:
            try :
                return ",".join(fk.columns)
            except Exception as  ex:
                logger.error(ex, exc_info=True)
        elif col == 2:
            return fk.reference_table
        elif col == 3:
            return ",".join(fk.reference_columns)
        elif col == 4:
            return fk.on_update
        elif col == 5:
            return fk.on_delete

        return ""

    def SetValueByRow(self, value, row, col):
        if row >= len(self.data):
            return False

        org_fk = self.get_data_by_row(row)
        new_fk = org_fk.copy()

        if col == 0:
            new_fk.name = value.Text
        elif col == 1:
            new_fk.columns = [c.strip() for c in value.split(",") if c.strip()]
        elif col == 2:
            new_fk.reference_table = value
        elif col == 3:
            new_fk.reference_columns = [c.strip() for c in value.split(",") if c.strip()]
        elif col == 4:
            new_fk.on_update = value
        elif col == 5:
            new_fk.on_delete = value

        if new_fk.name == "" and len(new_fk.columns) > 0 and new_fk.reference_table != "" and len(new_fk.reference_columns) > 0:
            table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()
            new_fk.name = f"fk_{table.name}_{'_'.join(new_fk.columns)}-{new_fk.reference_table}_{'_'.join(new_fk.reference_columns)}"

        if new_fk.is_valid and new_fk != org_fk:
                self.set_data_by_row(row, new_fk)
                self.ItemChanged(self.GetItem(row))

        return True


class TableForeignKeyController:
    def __init__(self, list_ctrl_foreign_key: TableForeignKeysDataViewCtrl):
        self.list_ctrl_foreign_key = list_ctrl_foreign_key

        self.model = TableForeignKeyModel(6)
        self.list_ctrl_foreign_key.AssociateModel(self.model)

        self.list_ctrl_foreign_key.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_foreign_key.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        self.list_ctrl_foreign_key.on_foreign_key_insert = self.on_foreign_key_insert
        self.list_ctrl_foreign_key.on_foreign_key_delete = self.on_foreign_key_delete

        CURRENT_TABLE.subscribe(self._load_table)
        NEW_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        with Loader.cursor_wait():
            self.model.clear()
            if table := NEW_TABLE.get_value() or CURRENT_TABLE.get_value():
                self.model.set_observable(table.foreign_keys)

    def _do_edit(self, item, column_index: int = 1):
        column = self.list_ctrl_foreign_key.GetColumn(column_index)
        self.list_ctrl_foreign_key.edit_item(item, column)

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        CURRENT_FOREIGN_KEY.set_value(None)

        if item.IsOk():
            foreign_key = self.model.get_data_by_item(item)
            CURRENT_FOREIGN_KEY.set_value(foreign_key)

        event.Skip()

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON FOREIGN KEY EDITING DONE {'#' * 10}")

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_foreign_keys: List[SQLForeignKey] = self.model.data

        table: SQLTable = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())
        original_foreign_keys: List[SQLForeignKey] = list(table.foreign_keys)

        map_foreign_keys = merge_original_current(original_foreign_keys, current_foreign_keys)

        if not all([o == c for o, c in map_foreign_keys]):
            table.foreign_keys.set_value(current_foreign_keys)

            NEW_TABLE.set_value(table)

        event.Skip()

    def on_foreign_key_insert(self, event : wx.Event):
        session = CURRENT_SESSION.get_value()
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        index = len(table.foreign_keys)

        new_empty_foreign_key = session.context.build_empty_foreign_key(
            name="",
            table=table,
            columns=[]
        )

        table.foreign_keys.append(new_empty_foreign_key)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_foreign_key.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

    def on_foreign_key_delete(self, event : wx.Event):
        selected = self.list_ctrl_foreign_key.GetSelection()
        if not selected.IsOk():
            return

        row = self.model.GetRow(selected)
        foreign_key = self.model.get_data_by_row(row)

        table = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())
        if foreign_key in table.foreign_keys:
            table.foreign_keys.remove(foreign_key)

            NEW_TABLE.set_value(table)

    def on_foreign_key_clear(self, event : wx.Event):
        table = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())

        self.model.clear()

        table.foreign_keys.clear()

        NEW_TABLE.set_value(table)
