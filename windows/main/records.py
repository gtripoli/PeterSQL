import wx.dataview

from helpers.logger import logger

from models.session import Session
from models.structures.database import SQLTable
from models.structures.datatype import DataTypeCategory

from windows.main import CURRENT_TABLE, CURRENT_SESSION


class RecordsModel(wx.dataview.DataViewIndexListModel):
    def __init__(self, session: Session, table: SQLTable, records: list):
        super().__init__(len(records))
        self.session = session
        self.table = table
        self.records = records

    def GetColumnCount(self):
        return len(self.table.columns)

    def GetValueByRow(self, row, col):
        column = self.table.columns[col]
        column_name = self.table.columns[col].name

        value = self.records[row].get(column_name, "")

        if column.datatype:
            if column.datatype.category == DataTypeCategory.TEMPORAL:
                return value

            elif column.datatype.name == "BOOLEAN":
                return bool(value == 1)

            elif column.datatype.category == DataTypeCategory.INTEGER:
                return int(value)

            elif column.datatype.category == DataTypeCategory.REAL:
                return float(value)

        return str(value)

    def SetValueByRow(self, value, row, col):
        column_name = self.table.columns[col].name

        self.records[row][column_name] = value

        return True


class TableRecordsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_records: wx.dataview.DataViewCtrl):
        self.list_ctrl_records = list_ctrl_records

        CURRENT_SESSION.subscribe(self._load_session)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Session):
        self.session = session

    def _load_table(self, table: SQLTable):
        if table is not None:
            self.table = table

            records = list(self.session.statement.get_records(table=table))
            model = RecordsModel(self.session, table, records)
            self.list_ctrl_records.AssociateModel(model)

    def refresh_records(self):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            records = list(self.session.statement.get_records(table=self.table))
            model = RecordsModel(self.table, records)
            self.list_ctrl_records.AssociateModel(model)

    def get_selected_record(self):
        selected_row = self.list_ctrl_records.GetSelectedRow()
        if selected_row != -1:
            return self.list_ctrl_records.GetModel().records[selected_row]
        return None

    def get_selected_records(self):
        selected_rows = self.list_ctrl_records.GetSelectedRows()
        if selected_rows:
            return [self.list_ctrl_records.GetModel().records[row] for row in selected_rows]
        return []

    def delete_selected_records(self):
        selected_rows = self.list_ctrl_records.GetSelectedRows()
        if selected_rows:
            for row in reversed(selected_rows):
                del self.list_ctrl_records.GetModel().records[row]
            self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
            self.list_ctrl_records.Refresh()

    def add_record(self, record):
        self.list_ctrl_records.GetModel().records.append(record)
        self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
        self.list_ctrl_records.Refresh()

    def update_record(self, row, record):
        if row < 0 or row >= len(self.list_ctrl_records.GetModel().records):
            return
        self.list_ctrl_records.GetModel().records[row] = record
        self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
        self.list_ctrl_records.Refresh()

    def save_changes(self):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            self.session.statement.save_changes(table=self.table, records=self.list_ctrl_records.GetModel().records)

    def export_records(self, file_path):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            records = self.list_ctrl_records.GetModel().records
            with open(file_path, 'w') as file:
                for record in records:
                    file.write(str(record) + '\n')

    def import_records(self, file_path):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            try:
                with open(file_path, 'r') as file:
                    records = [eval(line.strip()) for line in file.readlines()]
                    self.list_ctrl_records.GetModel().records.extend(records)
                    self.list_ctrl_records.GetModel().Reset(len(self.list_ctrl_records.GetModel().records))
                    self.list_ctrl_records.Refresh()
            except Exception as ex:
                logger.error(f"Error importing records: {ex}", exc_info=True)

    def filter_records(self, filter_func):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            records = list(filter(filter_func, self.list_ctrl_records.GetModel().records))
            model = RecordsModel(self.table, records)
            self.list_ctrl_records.AssociateModel(model)

    def sort_records(self, sort_func):
        if hasattr(self, 'session') and hasattr(self, 'table'):
            records = sorted(self.list_ctrl_records.GetModel().records, key=sort_func)
            model = RecordsModel(self.table, records)
            self.list_ctrl_records.AssociateModel(model)
