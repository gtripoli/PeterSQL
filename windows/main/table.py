import re
import copy
import dataclasses
from collections import Counter

from typing import List, Optional, Tuple

import wx
import wx.dataview

import sqlalchemy as sa
import sqlalchemy.sql.elements

from helpers.logger import logger
from helpers.bindings import AbstractModel
from helpers.observables import Observable, debounce, ObservableArray

from models.session import Session, SessionEngine
from models.structures import SQLDataType, DataTypeCategoryColor
from models.structures.charset import COLLATION_CHARSETS

from models.structures.mysql.datatype import MySQLDataType
from models.structures.mariadb.datatype import MariaDBDataType
from models.structures.sqlite.datatype import SQLiteDataType

from windows.main import CURRENT_TABLE, CURRENT_SESSION, CURRENT_DATABASE, CURRENT_COLUMN

NEW_TABLE: Observable[sa.Table] = Observable()
NEW_COLUMN: Observable[sa.Column] = Observable()


@dataclasses.dataclass
class ColumnModelData:
    id: str
    name: str = ""
    data_type: Optional[str] = ""
    length_set: Optional[str] = ""
    unsigned: bool = False
    nullable: bool = True
    zerofill: bool = False
    default: Optional[str] = None
    virtuality: Optional[str] = ""
    expression: Optional[str] = ""
    collation: Optional[str] = ""
    comments: str = ""
    primary_key: bool = False
    index_summary: Counter = None


class ColumnModel(wx.dataview.DataViewIndexListModel):
    COLUMN_FIELDS = [f.name for f in dataclasses.fields(ColumnModelData)]

    def __init__(self, engine_data_type):
        super().__init__()
        self.data: List[ColumnModelData] = []
        self.engine_data_type = engine_data_type

    def GetValueByRow(self, row, col):
        try:
            # print(ColumnModel.COLUMN_FIELDS[col], getattr(self.data[row], ColumnModel.COLUMN_FIELDS[col]))
            return getattr(self.data[row], ColumnModel.COLUMN_FIELDS[col])
        except Exception as ex:
            logger.error(ex, exc_info=True)

    def GetAttrByRow(self, row, col, attr):
        column_model_data: ColumnModelData = self.data[row]
        if column_model_data.primary_key :
            attr.SetBold(True)

        if col == 0:
            attr.SetBackgroundColour(wx.Colour(241, 241, 241))
            return True

        if col in [2, 7]:
            color = DataTypeCategoryColor[self.engine_data_type.get_by_name(column_model_data.data_type).category.value].value

            attr.SetColour(wx.Colour(color))
            return True

        return super().GetAttrByRow(row, col, attr)

    def SetValueByRow(self, value, row, col):
        item = self.GetItem(row)

        setattr(self.data[row], ColumnModel.COLUMN_FIELDS[col], value)

        self.ValueChanged(item, col)

        self._update_columns(col, row)

        return True

    def _update_columns(self, col, row):
        item = self.GetItem(row)

        length_set_value = ""
        column_model_data: ColumnModelData = self.data[row]

        if column_model_data.data_type is not None and col == 3:
            data_type: SQLDataType = self.engine_data_type.get_by_name(column_model_data.data_type)

            if data_type.has_set:
                length_set_value = data_type.default_set

            elif data_type.has_length:
                length_set_value = [data_type.default_length]
                if data_type.has_scale:
                    length_set_value.append(data_type.default_scale)

            if data_type.has_length or data_type.has_set:
                if isinstance(length_set_value, list):
                    length_set_value = ','.join(map(str, length_set_value))

            column_model_data.length_set = length_set_value

            self.ValueChanged(item, 3)

            if not data_type.has_unsigned:
                column_model_data.unsigned = False

                self.ValueChanged(item, 4)

            if not data_type.has_zerofill:
                column_model_data.zerofill = False
                self.ValueChanged(item, 5)

    def add_row(self, data: ColumnModelData) -> wx.dataview.DataViewItem:
        self.data.append(data)
        new_row_index = len(self.data) - 1
        self.RowAppended()
        return self.GetItem(new_row_index)

    def add_empty_row(self) -> wx.dataview.DataViewItem:
        column_model_data = ColumnModelData(id=str(len(self.data) + 1))
        return self.add_row(column_model_data)

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

    def _load_table(self, table: sa.Table):
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
            new_table = sa.Table(
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
        # self.list_ctrl_table_columns.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE, self.on_editing_done)
        self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.on_item_changed)

        CURRENT_SESSION.subscribe(self._load_session)
        # CURRENT_DATABASE.subscribe(self._update_columns)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Session):
        self.session = session

        if self.session.engine == SessionEngine.MYSQL:
            self.engine_data_type = MySQLDataType()
        elif self.session.engine == SessionEngine.MARIADB:
            self.engine_data_type = MariaDBDataType
        elif self.session.engine == SessionEngine.SQLITE:
            self.engine_data_type = SQLiteDataType()

        self.model = ColumnModel(self.engine_data_type)
        self.list_ctrl_table_columns.AssociateModel(self.model)

    def _normalize_column_default(self, value: str) -> str:
        """Remove surrounding quotes if present."""
        if not value:
            return ""
        value = re.sub(r"""^(["'])(.*)\1$""", r"\2", value)
        if value.strip() == "":
            return ""
        else:
            return value

    def _get_column_default(self, column) -> Tuple[str, str, str]:
        default = ""
        expression = ""
        virtuality = ""

        if column.autoincrement is True:
            default = "AUTO_INCREMENT"

        else:
            if (server_default := getattr(column, "server_default", None)) is not None:
                if (arg := getattr(server_default, "arg", None)) is not None:
                    default = self._normalize_column_default(arg.text)

                elif (sqltext := getattr(server_default, "sqltext", None)) is not None and hasattr(column, "computed"):
                    default = str(sqltext.type)
                    expression = sqltext.text
                    virtuality = "VIRTUAL" if not column.computed.persisted else "PERSISTENT"

        return default, expression, virtuality

    def _get_length_scale_set(self, column, data_type) -> str:
        """
        Return formatted length/scale/set string depending on the SQLDataType.
        """
        candidates = [
            (data_type.has_display_width, "display_width", str),
            (data_type.has_length, "length", str),
            (data_type.has_precision, "precision", str),
            (data_type.has_set, "enums", lambda v: ",".join(v)),
        ]

        length_scale_set = ""

        for condition, attr, transform in candidates:
            if condition and (value := getattr(column.type, attr, None)) is not None:
                length_scale_set = transform(value)
                break

        if data_type.has_scale and (scale := getattr(column.type, "scale", None)) is not None:
            length_scale_set += f"/{scale}"

        return length_scale_set

    def _column_index_summary(self, table, col: sa.Column) -> Counter:
        summary = Counter()

        for constraint in table.constraints:
            if isinstance(constraint, sa.UniqueConstraint) and col in list(constraint.columns):
                summary["unique_constraint"] += 1

        for idx in table.indexes:
            if col not in list(idx.columns):
                continue

            if idx.unique:
                summary["unique_index"] += 1
            else:
                summary["normal_index"] += 1

            mysql_opts = idx.dialect_options.get("mysql", {})
            if mysql_opts.get("fulltext"):
                summary["fulltext_index"] += 1
            if mysql_opts.get("spatial"):
                summary["spatial_index"] += 1

        return summary

    def _load_table(self, table: sa.Table):
        with self.app.cursor_wait():
            self.model.clear()

            for index, column in enumerate(table.columns, 1):
                data_type = self.engine_data_type.get_by_type(column.type)

                length_scale_set = self._get_length_scale_set(column, data_type)

                default, expression, virtuality = self._get_column_default(column)

                print("default", default)

                self.model.add_row(
                    ColumnModelData(
                        id=str(index),
                        name=column.name,
                        data_type=data_type.name,
                        length_set=length_scale_set,
                        unsigned=bool(data_type.has_unsigned and getattr(column.type, "unsigned", False)),
                        nullable=bool(column.nullable),
                        zerofill=bool(data_type.has_zerofill and getattr(column.type, "zerofill", False)),
                        primary_key=bool(column.primary_key),
                        default=default,
                        collation=getattr(column.type, "collation", None) or "",
                        virtuality=virtuality,  # Virtuality
                        expression=expression,
                        comments=column.comment or "",
                        index_summary=self._column_index_summary(table, column)
                    ))

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
        # event.Skip()

    def on_insert_column(self):
        item = self.model.add_empty_row()
        self.list_ctrl_table_columns.Select(item)

        self._edit_column(item, 1)

    def on_item_changed(self, event: wx.dataview.DataViewEvent):
        item = event.GetItem()

        print("on_editing_done")

        if not item.IsOk():
            event.Skip()
            return

        column = event.GetColumn()
        value = self.model.GetValue(item, column)

        print("CURRENT:", "column", column, "value", value)

        editable_columns = [column.ModelColumn for column in self.list_ctrl_table_columns.GetColumns() if wx.dataview.DATAVIEW_CELL_EDITABLE & column.Flags]

        if column == 2:
            data_type: SQLDataType = self.engine_data_type.get_by_name(value)
            if not all([data_type.has_length, data_type.has_set]):
                self.list_ctrl_table_columns.GetColumn(3).SetFlag(wx.dataview.DATAVIEW_CELL_INERT)
                self.model.SetValue("", item, 3)
                self.model.ValueChanged(item, 3)

            if not data_type.has_unsigned:
                self.list_ctrl_table_columns.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_CELL_INERT)
                self.model.SetValue(False, item, 4)
                self.model.ValueChanged(item, 4)

            if not data_type.has_zerofill:
                self.list_ctrl_table_columns.GetColumn(5).SetFlag(wx.dataview.DATAVIEW_CELL_INERT)
                self.model.SetValue(False, item, 5)
                self.model.ValueChanged(item, 5)

            # Forza il refresh della cella collation
            self.list_ctrl_table_columns.Refresh()

        idx = min(len(editable_columns) - 1, column + 1)

        if idx < len(editable_columns) - 1:
            self._edit_column(item, idx)

        # self.do_build(item) # TODO: reactive this

        event.Skip()

    def do_build(self, item: wx.dataview.DataViewItem):
        model_data: ColumnModelData = self.model.data[self.model.GetRow(item)]

        data_type = self.engine_data_type.get_by_name(model_data.data_type) if model_data.data_type is not None else None

        if data_type is not None:
            sa_column_kwargs = {}
            sa_data_type_kwargs = {}

            if data_type.has_length and model_data.length_set != '':
                sa_data_type_kwargs["length"] = int(model_data.length_set)

                if data_type.has_scale:
                    sa_data_type_kwargs["precision"] = int(0)

            if data_type.has_unsigned and model_data.unsigned:
                sa_data_type_kwargs["unsigned"] = True

            if data_type.has_zerofill and model_data.zerofill:
                sa_data_type_kwargs["zerofill"] = True

            if data_type.has_collation and model_data.collation != "":
                sa_data_type_kwargs["charset"] = COLLATION_CHARSETS[model_data.collation]
                sa_data_type_kwargs["collation"] = model_data.collation

            if model_data.default != None:
                if model_data.default == "AUTO_INCREMENT":
                    sa_column_kwargs["autoincrement"] = True
                elif model_data.default == "NULL":
                    sa_column_kwargs["server_default"] = sa.sql.elements.TextClause('NULL')
                else:
                    sa_column_kwargs["server_default"] = model_data.default
            else:
                sa_column_kwargs["server_default"] = None

            if (current_column := CURRENT_COLUMN.get_value()) is None:

                new_column = sa.Column(
                    model_data.name,
                    data_type.sa_type(**sa_data_type_kwargs),
                    # is_unsigned=is_unsigned,
                    nullable=model_data.nullable,

                    comment=model_data.comments,
                    **sa_column_kwargs
                    # generation_expression=generation_expression
                )
            else:
                modified_column: sa.Column = copy.copy(current_column)
                modified_column.name = model_data.name
                modified_column.data_type = data_type.sa_type(**sa_data_type_kwargs),

                for key, value in sa_column_kwargs.items():
                    setattr(modified_column, key, value)

                modified_column.nullable = model_data.nullable

                new_column = modified_column if modified_column.is_valid() and modified_column != current_column else None

            if all([new_column.name, new_column.type]):
                self._do_update_table(new_column)

    def _do_update_table(self, column: sa.Column):
        table = None
        if (new_table := NEW_TABLE.get_value()) is not None:
            table = copy.copy(new_table)
        elif (current_table := CURRENT_TABLE.get_value()) is not None:
            table = copy.copy(current_table)

        table.append_column(column, replace_existing=True)

        # if new_table is not None:
        NEW_TABLE.set_value(table)
        # NEW_TABLE.execute_callback(Observable.CallbackEvent.AFTER_CHANGE)
        # elif current_table is not None:
        # CURRENT_TABLE.set_value(None)
        # CURRENT_TABLE.execute_callback(Observable.CallbackEvent.AFTER_CHANGE)
