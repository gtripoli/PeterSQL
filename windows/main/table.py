import copy

from typing import List, Optional

import wx
import wx.dataview

from helpers.bindings import AbstractModel
from helpers.logger import logger
from helpers.observables import Observable, debounce, ObservableArray, Loader
from models.structures.indextype import SQLIndexType

from windows.main import CURRENT_SESSION, CURRENT_TABLE, CURRENT_DATABASE, CURRENT_COLUMN

from models.session import Session
from models.structures.database import SQLTable, SQLColumn, SQLIndex

NEW_TABLE: Observable[SQLTable] = Observable()
NEW_COLUMN: Observable[SQLColumn] = Observable()


class ColumnModel(wx.dataview.DataViewIndexListModel):
    MAP_COLUMN_FIELDS = {
        0: {"attr": "id", "transform": str},
        1: {"attr": "name", "transform": str},
        2: {"attr": "datatype", "transform": str},
        3: {"attr": "length_scale_set", "transform": str},
        4: {"attr": "is_unsigned", "transform": bool},
        5: {"attr": "is_nullable", "transform": bool},
        6: {"attr": "is_zerofill", "transform": bool},
        7: {"attr": "default", "transform": str},
        8: {"attr": "virtuality", "transform": str},
        9: {"attr": "expression", "transform": str},
        10: {"attr": "collation_name", "transform": str},
        11: {"attr": "comment", "transform": str},
    }

    def __init__(self, session: Session):
        super().__init__()
        self.data: List[SQLColumn] = []
        self.session = session

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        try:
            column_field = self.MAP_COLUMN_FIELDS[col]
        except Exception as ex:
            logger.error(ex)
            return None

        value = getattr(self.data[row], column_field['attr'])

        if value is None:
            return ""

        return column_field['transform'](value)

    def SetValueByRow(self, value, row, col):
        item = self.GetItem(row)

        column_field = ColumnModel.MAP_COLUMN_FIELDS[col]

        setattr(self.data[row], column_field['attr'], value)

        self.ValueChanged(item, col)

        self._update_columns(col, row)

        return True

    def GetAttrByRow(self, row, col, attr):
        if not len(self.data): return False
        column = self.data[row]

        if column.is_primary_key:
            attr.SetBold(True)

        if col == 0:
            attr.SetBackgroundColour(wx.Colour(241, 241, 241))
            return True

        if col in [2, 7]:
            color = column.datatype.category.value.color

            attr.SetColour(wx.Colour(color))
            return True

        return super().GetAttrByRow(row, col, attr)

    def _update_columns(self, col, row):
        item = self.GetItem(row)

        column = self.data[row]

        if column.datatype is not None and col == 3:
            if not column.datatype.has_unsigned:
                column.is_unsigned = False

                self.ValueChanged(item, 4)

            if not column.datatype.has_zerofill:
                column.is_zerofill = False
                self.ValueChanged(item, 5)

    def add_row(self, data: SQLColumn) -> wx.dataview.DataViewItem:
        self.data.append(data)
        new_row_index = len(self.data) - 1
        self.RowAppended()
        return self.GetItem(new_row_index)

    def add_empty_row(self) -> wx.dataview.DataViewItem:
        column = SQLColumn(
            id=int(len(self.data) + 1),
            name="",
            datatype=self.session.datatype.VARCHAR,
            table=CURRENT_TABLE.get_value()
        )
        return self.add_row(column)

    def del_row(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)
        del self.data[row]
        self.RowDeleted(row)

    def move_up(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)
        if row == 0:
            return
        self.data[row].id -= 1
        self.data[row - 1].id += 1
        self.data[row - 1], self.data[row] = self.data[row], self.data[row - 1]

        self.RowChanged(row - 1)
        self.RowChanged(row)
        return self.GetItem(row - 1)

    def move_down(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)
        if row == len(self.data) - 1:
            return
        self.data[row].id += 1
        self.data[row + 1].id -= 1
        self.data[row], self.data[row + 1] = self.data[row + 1], self.data[row]

        self.RowChanged(row + 1)
        self.RowChanged(row)
        return self.GetItem(row + 1)

    def clear(self):
        self.data = []
        self.Reset(0)
        self.Cleared()


class EditTableModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.comment = Observable()
        self.columns = ObservableArray()

        self.auto_increment = Observable()
        self.collation = Observable()
        self.engine = Observable()

        debounce(
            self.name, self.comment, self.auto_increment, self.collation, self.engine,
            callback=self.build_table
        )

        CURRENT_TABLE.subscribe(self._load_table)

    def _load_table(self, table: SQLTable):
        self.name.set_value(table.name if table is not None else "")
        self.comment.set_value(table.comment if table is not None else "")
        # self.auto_increment.set_value(table.auto_increment if table is not None else 0)
        # self.collation.set_value(table.collation if table is not None else "")
        # self.engine.set_value(table.engine if table is not None else "")

    def build_table(self, *args):
        if not any(args):
            return
        if (current_table := CURRENT_TABLE.get_value()) is None:
            session = CURRENT_SESSION.get_value()
            database = CURRENT_DATABASE.get_value()
            new_table = session.statement.build_new_table(database)
        else:
            new_table = copy.copy(current_table)

        new_table.name = self.name.get_value()
        new_table.comment = self.comment.get_value()
        new_table.collation = self.collation.get_value()
        new_table.auto_increment = self.auto_increment.get_value()

        logger.info(f"Building table: {new_table}")

        NEW_TABLE.set_value(new_table)


class ListTableColumnsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_table_columns: wx.dataview.DataViewCtrl):
        self.list_ctrl_table_columns = list_ctrl_table_columns
        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_value_changed)
        self.list_ctrl_table_columns.Bind(wx.EVT_SCROLL, self._on_scroll)
        # self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE, self._on_editing_done)

        self.list_ctrl_table_columns.on_column_insert = self.on_column_insert
        self.list_ctrl_table_columns.on_column_delete = self.on_column_delete
        self.list_ctrl_table_columns.on_column_move_up = self.on_column_move_up
        self.list_ctrl_table_columns.on_column_move_down = self.on_column_move_down

        self.list_ctrl_table_columns.on_index_create = self.on_index_create
        self.list_ctrl_table_columns.on_index_insert = self.on_index_insert

        CURRENT_SESSION.subscribe(self._load_session, execute_immediately=True)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Session):
        self.session = session
        self.model = ColumnModel(self.session)
        self.list_ctrl_table_columns.AssociateModel(self.model)

    def _load_table(self, table: SQLTable):
        with Loader.cursor_wait():
            self.model.clear()
            if table is not None:
                for index, column in enumerate(table.columns, 1):
                    self.model.add_row(column)

                self.model.Reset(len(table.columns))

            self.list_ctrl_table_columns.Refresh()

    def _edit_column(self, item, column_index: int = 1):
        wx.CallAfter(
            self.list_ctrl_table_columns.EditItem, item, self.list_ctrl_table_columns.GetColumn(column_index)
        )

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        if not item.IsOk():
            CURRENT_COLUMN.set_value(None)
        else:
            CURRENT_COLUMN.set_value(self.model.GetValue(item, 0))
        event.Skip()

    def on_key_down(self, event: wx.KeyEvent):
        print("key_down")
        key_code = event.GetKeyCode()
        shift_down = event.ShiftDown()

        item = self.list_ctrl_table_columns.GetSelection()
        column = self.list_ctrl_table_columns.GetCurrentColumn()
        column_model = column.ModelColumn
        # column_value = self.model.GetValue(item, column_model)

        if key_code == wx.WXK_TAB:
            self._next_edit_direction = -1 if shift_down else 1
            event.Skip()
            return
        elif key_code == wx.WXK_RETURN:
            # Solo chiude l’editor se non è una select
            self._next_edit_direction = 0  # nessun movimento
            event.Skip()
            return

        # print('---->', column_value)
        #
        #
        # if key_code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
        #     if column_model in editable_columns :
        #
        #         if isinstance(column_value, bool):
        #             self.model.SetValue(not column_value, item, column_model)
        #             self.model.ValueChanged(item, column_model)
        #
        #     event.Skip()
        #     return
        #
        # if key_code == wx.WXK_SPACE:
        #     if isinstance(column_value, bool):
        #         self.model.SetValue(not column_value, item, column_model)
        #         self.model.ValueChanged(item, column_model)
        #         return
        #
        #
        # if key_code == wx.WXK_TAB:
        #     # if not item.IsOk():
        #     #     return
        #
        #     if shift_down:
        #         idx = max(0, column_model - 1)
        #     else:
        #         idx = min(len(editable_columns) - 1, column_model + 1)
        #
        #     print('ModelColumn', column.ModelColumn, 'idx', idx, 'value', column_value, "next:", self.list_ctrl_table_columns.GetColumn(idx).Title)
        #
        #     # self.model.SetValue(column_value, item, column_model)
        #
        #     wx.CallAfter(self.list_ctrl_table_columns.CloseEditor)
        #     self._edit_column(item, idx)
        #
        #
        event.Skip()

    def on_column_insert(self):
        item = self.model.add_empty_row()
        self.list_ctrl_table_columns.Select(item)

        self._edit_column(item, 1)

    def on_column_delete(self):
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return
        self.model.del_row(selected)
        self.do_refresh_table()

    def on_column_move_up(self):
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        if item := self.model.move_up(selected):
            self.do_refresh_table()
            self.list_ctrl_table_columns.Select(item)

    def on_column_move_down(self):
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return
        if item := self.model.move_down(selected):
            self.do_refresh_table()
            self.list_ctrl_table_columns.Select(item)

    def on_index_create(self, event, index_type: SQLIndexType):
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return

        table = CURRENT_TABLE.get_value()

        row = self.model.GetRow(selected)
        col = self.model.data[row]

        counter = 1
        indexes = [index.name for index in table.indexes]
        while (name := f"{index_type.prefix}_{table.name}_{col.name}_{str(counter).zfill(3)}") in indexes:
            counter += 1

        # name = f"{index_type.lower()}_{col.name}" if not is_primary else "PRIMARY"
        new_index = SQLIndex(name=name, type=index_type, columns=[col.name])
        table.indexes.append(new_index)

        self.do_refresh_table()

        return True

    def on_index_insert(self, event: wx.Event, index: SQLIndex) -> Optional[bool]:
        selected = self.list_ctrl_table_columns.GetSelection()
        if not selected.IsOk():
            return
        row = self.model.GetRow(selected)
        col = self.model.data[row]
        index.columns.append(col.name)

        self.do_refresh_table()

        return True

    def on_index_delete(self):
        # selected = self.list_ctrl_table_columns.GetSelection()
        pass

    def _on_value_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON_EDITING_DONE", "#" * 10)

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        column = event.GetColumn()
        value = self.model.GetValue(item, column)

        if column == 2:
            datatype = self.session.datatype.get_by_name(value)

            self.model.SetValue("", item, 3)

            if datatype is not None:
                if not any([datatype.has_length, datatype.has_precision, datatype.has_set]):
                    # self.list_ctrl_table_columns.GetColumn(3).GetRenderer().GetEditorCtrl().Enable(False)
                    pass

                if not datatype.has_unsigned:
                    # self.list_ctrl_table_columns.GetColumn(4).GetRenderer().GetEditorCtrl().Enable(False)
                    self.model.SetValue(False, item, 4)

                if not datatype.has_zerofill:
                    # self.list_ctrl_table_columns.GetColumn(4).GetRenderer().GetEditorCtrl().Enable(False)
                    self.model.SetValue(False, item, 5)

                if datatype.has_collation and (collation := datatype.default_collation) is not None:
                    self.model.SetValue(collation, item, 10)

        self.list_ctrl_table_columns.Refresh()

        editable_columns = [
            c.ModelColumn
            for c in self.list_ctrl_table_columns.GetColumns()
            if c.ModelColumn > column and c.HasFlag(wx.dataview.DATAVIEW_CELL_EDITABLE)
        ]

        idx = min(editable_columns)

        if idx < len(editable_columns) - 1:
            self._edit_column(item, idx)

        self.do_build(item)

        event.Skip()

    def do_build(self, item: wx.dataview.DataViewItem):
        column: SQLColumn = self.model.data[self.model.GetRow(item)]

        table: Optional[SQLTable] = CURRENT_TABLE.get_value() or NEW_TABLE.get_value()

        if table is not None:
            table.columns.append(column, replace_existing=True)

        NEW_TABLE.set_value(table)

    def do_refresh_table(self):
        columns: List[SQLColumn] = self.model.data

        table: Optional[SQLTable] = CURRENT_TABLE.get_value() or NEW_TABLE.get_value()

        if table is not None:
            table.columns.override(columns)

        NEW_TABLE.set_value(table)

    def _on_scroll(self, event):
        self.list_ctrl_table_columns.ProcessEvent(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE)
        event.Skip()
