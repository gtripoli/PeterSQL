import datetime
from typing import Optional, List, Union

import wx.dataview

from helpers.logger import logger

from engines.session import Session
from engines.structures.database import SQLTable, SQLDatabase, SQLColumn, SQLRecord
from engines.structures.datatype import DataTypeCategory
from helpers.observables import ObservableList
from windows import TableRecordsDataViewCtrl

from windows.main import CURRENT_TABLE, CURRENT_SESSION, CURRENT_DATABASE, AUTO_APPLY, CURRENT_RECORDS, BaseDataViewIndexListModel

NEW_RECORDS: ObservableList[SQLRecord] = ObservableList()


class RecordsModel(BaseDataViewIndexListModel):
    def __init__(self, table: SQLTable, column_count: Optional[int] = None):
        super().__init__(column_count)

        self.table: SQLTable = table

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        column = self.table.columns[col]

        record: SQLRecord = self.data[row]

        value = record.values.get(column.name, "")

        if value is None:
            return ''

        if not str(value).strip():
            return ''

        if column.datatype.category == DataTypeCategory.TEMPORAL:
            # if column.datatype.name == "DATE":
            #     return datetime.datetime.strptime(value, "%Y-%m-%d")
            # elif column.datatype.name == "TIME":
            #     return datetime.datetime.strptime(value, "%H:%M:%S")
            # elif column.datatype.name == "DATETIME":
            #     return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            # elif column.datatype.name == "TIMESTAMP":
            #     return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            # elif column.datatype.name == "YEAR":
            #     return datetime.datetime.strptime(value, "%Y")
            # print("TODO: transform this", column.datatype.category, value)

            return value

        elif column.datatype.name == "BOOLEAN":
            return bool(value == 1)

        return str(value)

    def SetValueByRow(self, value, row, col):
        item = self.GetItem(row)

        column: SQLColumn = self.table.columns[col]

        self.data[row].values[column.name] = value

        self.ValueChanged(item, col)

        return True

    def GetAttr(self, item, col, attr):
        column: SQLColumn = self.table.columns[col]

        color = column.datatype.category.value.color

        attr.SetColour(wx.Colour(color))

        if self.table.columns[col].is_primary_key:
            attr.SetBold(True)

        return super().GetAttr(item, col, attr)

    def add_row(self, data: SQLRecord) -> wx.dataview.DataViewItem:
        self.data.append(data)
        self.RowAppended()
        return self.GetItem(len(self.data) - 1)

    #
    # def del_row(self, item: wx.dataview.DataViewItem):
    #     row = self.GetRow(item)
    #     del self.data[row]
    #     self.RowDeleted(row)
    #
    # def clear(self):
    #     self.data = []
    #     self.Reset(0)
    #     self.Cleared()


class TableRecordsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_records: TableRecordsDataViewCtrl):
        self.list_ctrl_records = list_ctrl_records
        # self.list_ctrl_records.on_record_insert = self.on_insert_record
        # self.list_ctrl_records.on_record_delete = self.on_delete_record

        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        CURRENT_SESSION.subscribe(self._load_session, execute_immediately=True)
        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Session):
        self.session = session

    def _load_database(self, database: SQLDatabase):
        self.database = database

    def _load_table(self, table: SQLTable):
        if table is not None:
            self.table = table

            logger.debug(f"table {table}")
            logger.debug(f"table.records {table.records}")

            # records = list(table.get_records_handler(table, 1000, 0))
            # self.model = RecordsModel(self.session, table, records)
            self.model = RecordsModel(self.table, len(self.table.columns))
            self.model.set_observable(self.table.records)
            self.list_ctrl_records.AssociateModel(self.model)

    def _do_edit(self, item, model_column: int = 1):
        column = self.list_ctrl_records.GetColumn(model_column)

        wx.CallAfter(
            self.list_ctrl_records.EditItem, item, column
        )

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON RECORD EDITING DONE", "#" * 10)

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        record = self.model.data[self.model.GetRow(item)]

        if AUTO_APPLY.get_value() and record.is_valid():
            try:
                record.save()
            except Exception as ex:
                logger.error(f"Error saving record: {ex}", exc_info=True)

            else:
                records = list(self.session.context.get_records(table=self.table))
                self.table.records.set_value(records)
                # self.model.data = records
                # self.list_ctrl_records.refresh()

                # CURRENT_RECORDS.set_value(self.get_selected_records())

        else:
            NEW_RECORDS.append(record, replace_existing=True)

        event.Skip()

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON SELECTION CHANGED", "#" * 10)
        records = self.get_selected_records()
        print("records", records)
        CURRENT_RECORDS.set_value(self.get_selected_records())
        event.Skip()

    def get_selected_records(self):
        return [self.model.data[self.model.GetRow(row)] for row in self.list_ctrl_records.GetSelections()]

    def get_first_editable_column(self):
        for i, column in enumerate(self.table.columns):
            if not column.is_auto_increment and not column.server_default:
                return i

        return None

    def do_insert_record(self):
        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_records.GetSelection()

        index = len(table.records)
        values = dict()

        datatype = session.datatype.VARCHAR

        if selected:
            current_record: SQLRecord = self.model.get_data_by_item(selected)
            # datatype = current_column.datatype
            index = table.records.index(current_record) + 1

        column_server_default = {}
        for column in table.columns:
            if column.is_auto_increment:
                continue

            if column.server_default:
                if not column_server_default.get(column.server_default):
                    if table.context.execute(f"SELECT {column.server_default} as column_default"):
                        column_server_default[column.server_default] = table.context.fetchone()['column_default']

                values[column.name] = column_server_default[column.server_default]

        new_empty_record = session.context.build_empty_record(
            table=table,
            values=values
        )

        table.records.insert(index, new_empty_record)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_records.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

    def do_duplicate_record(self):
        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_records.GetSelection()

        if not selected.IsOk() :
            return

        index = len(table.records)
        values = dict()

        if selected:
            current_record: SQLRecord = self.model.get_data_by_item(selected)
            # datatype = current_column.datatype
            index = table.records.index(current_record) + 1

        column_server_default = {}
        for column in table.columns:
            if column.is_auto_increment:
                continue

            # if column.server_default:
            #     if not column_server_default.get(column.server_default):
            #         if table.context.execute(f"SELECT {column.server_default} as column_default"):
            #             column_server_default[column.server_default] = table.context.fetchone()['column_default']

            values[column.name] = current_record.values.get(column.name)

        new_empty_record = session.context.build_empty_record(
            table=table,
            values=values
        )

        table.records.insert(index, new_empty_record)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_records.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

        # item = self.model.add_empty_row()
        # self.list_ctrl_records.Refresh()
        #
        # column = self.list_ctrl_records.GetColumn(self.get_first_editable_column())
        # self.list_ctrl_records.EditItem(item, column)

    def do_delete_record(self):
        table = CURRENT_TABLE.get_value()

        records = CURRENT_RECORDS.get_value()

        SQLRecord.delete_many(table, records)

        CURRENT_RECORDS.set_value(None)

    # def update_record(self, row, record):
    #     if row < 0 or row >= len(self.list_ctrl_records.GetModel().records):
    #         return
    #     self.model.data[row] = record
    #     self.model.Reset(len(self.model.data))
    #     self.list_ctrl_records.Refresh()

    # def export_records(self, file_path):
    #     if hasattr(self, 'session') and hasattr(self, 'table'):
    #         records = self.list_ctrl_records.GetModel().records
    #             for record in records:
    #                 file.write(str(record) + '\n')
    #
    # def import_records(self, file_path):
    #     if hasattr(self, 'session') and hasattr(self, 'table'):
    #         try:
    #             with open(file_path, 'r') as file:
    #                 records = [eval(line.strip()) for line in file.readlines()]
    #                 self.list_ctrl_records.GetModel().records.extend(records)
    #                 self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
    #                 self.list_ctrl_records.Refresh()
    #         except Exception as ex:
    #             logger.error(f"Error importing records: {ex}", exc_info=True)
    #
    # def filter_records(self, filter_func):
    #     if hasattr(self, 'session') and hasattr(self, 'table'):
    #         records = list(filter(filter_func, self.list_ctrl_records.GetModel().records))
    #         model = RecordsModel(self.table, records)
    #         self.list_ctrl_records.AssociateModel(model)
    #
    # def sort_records(self, sort_func):
    #     if hasattr(self, 'session') and hasattr(self, 'table'):
    #         records = sorted(self.list_ctrl_records.GetModel().records, key=sort_func)
    #         model = RecordsModel(self.table, records)
    #         self.list_ctrl_records.AssociateModel(model)
