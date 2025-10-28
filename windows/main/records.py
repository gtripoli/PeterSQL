from datetime import datetime
from typing import List

import wx.dataview

from helpers.logger import logger

from models.session import Session
from models.structures.database import SQLTable, SQLDatabase, SQLColumn, SQLRecord
from models.structures.datatype import DataTypeCategory
from windows import TableRecordsDataViewCtrl

from windows.main import CURRENT_TABLE, CURRENT_SESSION, CURRENT_DATABASE, AUTO_APPLY, CURRENT_RECORDS


class RecordsModel(wx.dataview.DataViewIndexListModel):
    def __init__(self, session: Session, table: SQLTable, data: List[SQLRecord]):
        super().__init__(len(data))
        self.session: Session = session
        self.table: SQLTable = table
        self.data: List[SQLRecord] = data

    def GetCount(self):
        return len(self.data)

    def GetColumnCount(self):
        return len(self.table.columns)

    def GetColumnType(self, col):
        # column = self.table.columns[col]
        #
        # if column.datatype.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL]:
        #     return "number"

        return "string"

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        column = self.table.columns[col]
        # column.name

        record: SQLRecord = self.data[row]
        value = getattr(record, column.name, "")

        if value is None:
            return ''

        if column.datatype.category == DataTypeCategory.TEMPORAL:
            print("TODO: transform this", column.datatype.category, value)
            return value

        elif column.datatype.name == "BOOLEAN":
            return bool(value == 1)

        return str(value)

    def SetValueByRow(self, value, row, col):
        item = self.GetItem(row)

        column: SQLColumn = self.table.columns[col]

        print("SetValueByRow", row, col, value )
        setattr(self.data[row], column.name, value)

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

    def add_empty_row(self) -> wx.dataview.DataViewItem:
        record = SQLRecord(_id=-1, table=self.table)
        return self.add_row(record)

    def del_row(self, item: wx.dataview.DataViewItem):
        row = self.GetRow(item)
        del self.data[row]
        self.RowDeleted(row)

    def clear(self):
        self.data = []
        self.Reset(0)
        self.Cleared()


class TableRecordsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_records: TableRecordsDataViewCtrl):
        self.list_ctrl_records = list_ctrl_records
        # self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_select_record)
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

            records = list(table.get_records_handler(table, 1000, 0))
            self.model = RecordsModel(self.session, table, records)
            self.list_ctrl_records.AssociateModel(self.model)

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON RECORD EDITING DONE", "#" * 10)

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        record = self.model.data[self.model.GetRow(item)]
        print("record", record)
        if AUTO_APPLY.get_value():
            try:
                self.session.statement.save_record(self.database, self.table, record)
            except Exception as ex:
                logger.error(f"Error saving record: {ex}", exc_info=True)

            else:
                records = list(self.session.statement.get_records(table=self.table))
                self.model.data = records
                self.list_ctrl_records.refresh()

                CURRENT_RECORDS.set_value(self.get_selected_records())

        event.Skip()

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        print("#" * 10, "ON SELECTION CHANGED", "#" * 10)
        records = self.get_selected_records()
        print("records", records)
        CURRENT_RECORDS.set_value(self.get_selected_records())
        event.Skip()

    # def refresh_records(self):
    #     if hasattr(self, 'session') and hasattr(self, 'table'):
    #         records = list(self.session.statement.get_records(database=self.database, table=self.table))
    #         model = RecordsModel(self.session, self.table, records)
    #         self.list_ctrl_records.AssociateModel(model)

    def get_selected_records(self):
        return [self.model.data[self.model.GetRow(row)] for row in self.list_ctrl_records.GetSelections()]

    def get_first_editable_column(self):
        for i, column in enumerate(self.table.columns):
            if not column.is_auto_increment and not column.server_default:
                return i

        return None

    def on_insert_record(self):
        item = self.model.add_empty_row()
        self.list_ctrl_records.Refresh()

        column = self.list_ctrl_records.GetColumn(self.get_first_editable_column())
        self.list_ctrl_records.EditItem(item, column)
    #
    # def do_delete_record(self):
    #     selected_rows = self.list_ctrl_records.GetSelections()
    #
    #     if selected_rows:
    #         for row in reversed(selected_rows):
    #             del self.list_ctrl_records.GetModel().records[row]
    #         self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
    #         self.list_ctrl_records.Refresh()

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
