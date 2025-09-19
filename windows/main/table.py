import copy

from typing import List

import wx
import wx.dataview

from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce, ObservableArray, Loader

from windows.main import CURRENT_SESSION, CURRENT_TABLE

from models.session import Session
from models.structures.database import SQLTable, SQLColumn

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

        column_field = ColumnModel.MAP_COLUMN_FIELDS[col]

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
        column: SQLColumn = self.data[row]

        if column.is_primary:
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

        column: SQLColumn = self.data[row]

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
        column = SQLColumn(id=str(len(self.data) + 1), name="", datatype=self.session.datatype.VARCHAR)
        return self.add_row(column)

    def clear(self):
        self.data = []
        self.Cleared()


class EditTableModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.comment = Observable()
        self.columns = ObservableArray()

        self.auto_increment = Observable()
        self.collation = Observable()
        self.engine = Observable()

        CURRENT_TABLE.subscribe(self._load_table)

        debounce(
            self.name, self.comment, self.auto_increment, self.collation, self.engine,
            callback=self.build_table
        )

    def _load_table(self, table: SQLTable):
        self.name.set_value(table.name if table is not None else "")
        self.comment.set_value(table.comment if table is not None else "")
        # self.auto_increment.set_value(table.auto_increment if table is not None else 0)
        # self.collation.set_value(table.collation if table is not None else "")
        # self.engine.set_value(table.engine if table is not None else "")

    def build_table(self, *_args):
        new_table = None

        if (current_table := CURRENT_TABLE.get_value()) is None:
            # if self.engine.get_value() == SessionEngine.MYSQL.value and not any([
            #     self.name.is_empty, self.hostname.is_empty, self.username.is_empty, self.password.is_empty
            # ]):
            new_table = SQLTable(
                id=None,
                name=self.name.get_value(),
                comment=self.comment.get_value(),
                engine=self.engine.get_value(),
                collation=self.collation.get_value(),
                auto_increment=self.auto_increment.get_value(),

                count_rows=0
                #         comments=self.comments.get_value(),
                #         configuration=SessionMySQLConfiguration(
                #             hostname=self.hostname.get_value(),
                #             username=self.username.get_value(),
                #             password=self.password.get_value(),
                #             password=self.password.get_value(),
                #             port=self.port.get_value()
                #         )
            )
        # elif self.engine.get_value() == SessionEngine.SQLITE.value and not self.filename.is_empty:
        #     new_session = Session(
        #         id=None,
        #         name=self.name.get_value(),
        #         engine=SessionEngine(self.engine.get_value()),
        #         comments=self.comments.get_value(),
        #         configuration=SessionSQLiteConfiguration(
        #             filename=self.filename.get_value()
        #         )
        #     )
        else:
            modified = copy.copy(current_table)
            modified.name = self.name.get_value()
            modified.engine = self.engine.get_value()
            modified.comment = self.comment.get_value()
            modified.engine = self.engine.get_value(),
            modified.collation = self.collation.get_value(),
            modified.auto_increment = self.auto_increment.get_value(),

            # if modified.is_valid() and modified != current_table:
            #     new_table = modified

        NEW_TABLE.set_value(new_table)


class ListTableColumnsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_table_columns: wx.dataview.DataViewCtrl):
        self.list_ctrl_table_columns = list_ctrl_table_columns
        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_value_changed)
        self.list_ctrl_table_columns.Bind(wx.EVT_SCROLL, self._on_scroll)

        CURRENT_SESSION.subscribe(self._load_session)
        # CURRENT_DATABASE.subscribe(self._update_columns)
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

            # Reset the view to reflect the changes
            self.model.Reset(len(table.columns))

            self.list_ctrl_table_columns.Refresh()

    def _edit_column(self, item, column_index: int = 1):
        wx.CallAfter(
            self.list_ctrl_table_columns.EditItem, item, self.list_ctrl_table_columns.GetColumn(column_index)
        )

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

    def on_insert_column(self):
        item = self.model.add_empty_row()
        self.list_ctrl_table_columns.Select(item)

        self._edit_column(item, 1)

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

            self.model.SetValue(None, item, 3)

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

        table: SQLTable = CURRENT_TABLE.get_value()

        if table is not None:
            table.columns.append(column, replace_existing=True)

        NEW_TABLE.set_value(table)

    def _on_scroll(self, event):
        self.list_ctrl_table_columns.ProcessEvent(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE)
        event.Skip()
