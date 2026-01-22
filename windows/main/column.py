from typing import List, Optional, Dict, Any

import wx
import wx.dataview

from helpers.loader import Loader
from icons import combine_bitmaps

from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel, ColumnField

from windows import TableColumnsDataViewCtrl
from windows.main import CURRENT_CONNECTION, CURRENT_DATABASE, CURRENT_TABLE, CURRENT_COLUMN
from windows.main.table import NEW_TABLE

from structures.helpers import merge_original_current
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLDatabase
from structures.engines.indextype import SQLIndexType
from structures.connection import Connection


class ColumnModel(BaseDataViewListModel):
    MAP_COLUMN_FIELDS: Dict[int, ColumnField]

    def GetColumnCount(self):
        return len(self.MAP_COLUMN_FIELDS)

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        column: SQLColumn = self.get_data_by_row(row)
        column_field = self.MAP_COLUMN_FIELDS[col]
        column_field_value = column_field.get_value(column)

        if getattr(column_field, "attr") == "#":
            bitmaps = wx.NullBitmap
            if column.table:
                indexes = [i.type for i in column.table.indexes if column.name in i.columns ]

                indexes += [i for i in column.table.foreign_keys if column.name in i.columns]

                if len(indexes):
                    bitmaps = combine_bitmaps(*set([i.bitmap for i in indexes]))

            return wx.dataview.DataViewIconText(column_field_value, bitmaps)

        return column_field_value

    def SetValueByRow(self, value, row, col):
        item = self.GetItem(row)

        column_field = self.MAP_COLUMN_FIELDS[col]
        column_field_attr = getattr(column_field, "attr")

        org_col = self.get_data_by_row(row)
        new_col = org_col.copy()

        setattr(new_col, column_field_attr, value)

        if new_col != org_col:
            self.set_data_by_row(row, new_col)

            self.update_columns(col, row)

            self.ItemChanged(item)

        return True

    def GetAttrByRow(self, row, col, attr):
        if not len(self.data): return False

        column: SQLColumn = self.data[row]
        column_field = self.MAP_COLUMN_FIELDS[col]
        column_field_attr = getattr(column_field, "attr")

        if column.is_primary_key:
            attr.SetBold(True)

        if column_field_attr == "#":
            attr.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION))

        if column_field_attr == "name" and not getattr(column, column_field_attr, "").strip():
            attr.SetColour(wx.Colour(255, 0, 0))
            attr.SetItalic(True)

        if column_field_attr in ["datatype", "length_scale_set", "check", "default"]:
            color = column.datatype.category.value.color

            attr.SetColour(wx.Colour(color))

        if column_field_attr == "length_scale_set":
            datatype = column.datatype
            if not any([datatype.has_length, datatype.has_precision, datatype.has_scale, datatype.has_set]):
                attr.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVECAPTION))

        return True

    def update_columns(self, col, row):
        column: SQLColumn = self.get_data_by_row(row)

        column_field = self.MAP_COLUMN_FIELDS[col]
        column_field_attr = getattr(column_field, "attr")

        if column_field_attr == "datatype" and column.datatype is not None:
            length_precision_scale_set = [
                (column.datatype.has_length, "length", column.datatype.default_length),
                (column.datatype.has_precision, "numeric_precision", column.datatype.default_precision),
                (column.datatype.has_scale, "numeric_scale", column.datatype.default_scale),
                (column.datatype.has_set, "set", column.datatype.default_set)
            ]

            for condition, attr, default in length_precision_scale_set:
                setattr(column, attr, default if condition and not getattr(self, attr, None) else None)

            if not column.datatype.has_unsigned:
                column.is_unsigned = False

            if not column.datatype.has_zerofill:
                column.is_zerofill = False

        if column_field_attr == "is_nullable" and not column.is_nullable and column.default == "NULL":
            column.default = None

        if column_field_attr == "default" and column.default == "NULL" and not column.is_nullable:
            column.is_nullable = True


class TableColumnsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_table_columns: TableColumnsDataViewCtrl):
        self.list_ctrl_table_columns = list_ctrl_table_columns

        self.list_ctrl_table_columns.insert_column_index = self.insert_column_index
        self.list_ctrl_table_columns.append_column_index = self.append_column_index

        self.list_ctrl_table_columns.on_column_insert = self.on_column_insert
        self.list_ctrl_table_columns.on_column_delete = self.on_column_delete
        self.list_ctrl_table_columns.on_column_move_up = self.on_column_move_up
        self.list_ctrl_table_columns.on_column_move_down = self.on_column_move_down

        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)
        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_change)

        self.model = ColumnModel(None)
        self.list_ctrl_table_columns.AssociateModel(self.model)

        CURRENT_CONNECTION.subscribe(self._load_session)
        CURRENT_TABLE.subscribe(self._load_table)
        NEW_TABLE.subscribe(self._load_table)

    def _do_edit(self, item, model_column: int = 1):
        column = self.list_ctrl_table_columns.GetColumn(model_column)
        self.list_ctrl_table_columns.edit_item(item, column)

    def _load_session(self, session):
        with Loader.cursor_wait():
            if session is not None:
                self.model.MAP_COLUMN_FIELDS = session.context.MAP_COLUMN_FIELDS

    def _load_table(self, table: SQLTable):
        with Loader.cursor_wait():
            self.model.clear()
            if table := NEW_TABLE.get_value() or CURRENT_TABLE.get_value():
                self.model.set_observable(table.columns)

    def _on_selection_change(self, event):
        item = event.GetItem()

        CURRENT_COLUMN.set_value(None)

        if item.IsOk():
            column: SQLColumn = self.model.get_data_by_item(item)
            CURRENT_COLUMN.set_value(column)

        event.Skip()

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON COLUMN EDITING DONE {'#' * 10}")

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_columns: List[SQLColumn] = self.model.data

        table: SQLTable = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())

        database: SQLDatabase = CURRENT_DATABASE.get_value()

        if not table.is_new :
            original_table = next((t for t in list(database.tables) if t.id == table.id), None)
            original_columns = list(original_table.columns)
        else :
            original_columns = []

        map_columns = merge_original_current(original_columns, current_columns)

        if not all(o == c for o, c in map_columns):
            for original_column, current_column in map_columns:
                if original_column is None:
                    continue

                indexes = [i for i in table.indexes if original_column.name in i.columns]

                if current_column is None:
                    for index in indexes:
                        index.columns.remove(original_column.name)

                elif original_column.name != current_column.name:
                    for index in indexes:
                        p = index.columns.index(original_column.name)
                        index.columns.remove(original_column.name)
                        index.columns.insert(p, current_column.name)

            table.columns.set_value(current_columns)

            NEW_TABLE.set_value(table)

        event.Skip()

    def on_column_insert(self, event: wx.Event):
        session = CURRENT_CONNECTION.get_value()
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        selected = self.list_ctrl_table_columns.GetSelection()

        index = len(table.columns)
        default_values = dict()

        datatype = session.context.DATATYPE.VARCHAR

        if selected:
            current_column: SQLColumn = self.model.get_data_by_item(selected)
            datatype = current_column.datatype
            index = table.columns.index(current_column) + 1
            if hasattr(current_column, "after") :
                default_values["after"] = current_column.name

        if datatype.has_length:
            default_values['length'] = datatype.default_length
        if datatype.has_precision:
            default_values['precision'] = datatype.default_precision
        if datatype.has_scale:
            default_values['scale'] = datatype.default_scale
        if datatype.has_set:
            default_values['set'] = datatype.default_set

        new_empty_column = session.context.build_empty_column(
            table=table,
            datatype=datatype,
            **default_values
        )

        table.columns.insert(index, new_empty_column)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_table_columns.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

    def on_column_delete(self, event: wx.Event):
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        column: SQLColumn = self.model.get_data_by_item(selected)

        indexes = [i for i in table.indexes if column.name in i.columns]
        for index in indexes:
            index.columns.remove(column.name)
            if not len(index.columns):
                table.indexes.remove(index)

        table.columns.remove(column)

        NEW_TABLE.set_value(table)

    def on_column_move_up(self, event: wx.Event):
        table = NEW_TABLE.get_value() or CURRENT_TABLE.get_value()

        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        selected_column: SQLColumn = self.model.get_data_by_item(selected)
        selected_row = self.model.GetRow(selected)

        previous_row = selected_row - 1

        table.columns.move_up(selected_column)

        self.list_ctrl_table_columns.Select(self.model.GetItem(previous_row))

        CURRENT_COLUMN.set_value(None).set_value(selected_column)

    def on_column_move_down(self, event: wx.Event):
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        selected_column: SQLColumn = self.model.get_data_by_item(selected)
        selected_row = self.model.GetRow(selected)

        forward_row = selected_row + 1

        table.columns.move_down(selected_column)

        self.list_ctrl_table_columns.Select(self.model.GetItem(forward_row))

        CURRENT_COLUMN.set_value(None).set_value(selected_column)

    def insert_column_index(self, event: wx.Event, index_type: SQLIndexType):
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        session: Connection = CURRENT_CONNECTION.get_value()

        table = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())

        row = self.model.GetRow(selected)
        col = self.model.data[row]

        counter = 1
        indexes = [index.name for index in table.indexes]
        while (name := f"{index_type.prefix}{table.name}_{col.name}_{str(counter).zfill(3)}") in indexes:
            counter += 1

        new_index = session.context.build_empty_index(name=name, table=table, type=index_type, columns=[col.name])

        table.indexes.append(new_index)

        NEW_TABLE.set_value(table)

        return True

    def append_column_index(self, event: wx.Event, index: SQLIndex) -> Optional[bool]:
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        table = (NEW_TABLE.get_value() or CURRENT_TABLE.get_value())

        row = self.model.GetRow(selected)
        col = self.model.data[row]
        index.columns.append(col.name)

        table.indexes.append(index, replace_existing=True)

        NEW_TABLE.set_value(table)

        return True

    def on_index_delete(self):
        # selected = self.list_ctrl_table_columns.GetSelection()
        pass
