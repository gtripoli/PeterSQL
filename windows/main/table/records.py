import datetime

from typing import Optional

import wx.dataview
import wx.stc

from helpers.dataview import BaseObservableDataViewListModel
from helpers.logger import logger
from helpers.observables import ObservableList

from structures.session import Session
from structures.engines.database import SQLTable, SQLDatabase, SQLColumn, SQLRecord
from structures.engines.datatype import DataTypeCategory

from windows.views import TableRecordsDataViewCtrl

from windows.dialogs.column_content import ColumnContentDialogController

from windows.main import CURRENT_TABLE, CURRENT_SESSION, CURRENT_DATABASE, AUTO_APPLY, CURRENT_RECORDS
from windows.main.table.executor import RecordsExecutor, RecordsOperationResult

NEW_RECORDS: ObservableList[SQLRecord] = ObservableList()

NULL_DISPLAY = "NULL"


class RecordsModel(BaseObservableDataViewListModel):
    def __init__(self, table: SQLTable, column_count: Optional[int] = None):
        super().__init__(column_count)

        self.table: SQLTable = table

    def _load(self, data):
        super()._load([record.copy() for record in data])

    def _is_null(self, row, col):
        column = self.table.columns[col]
        record: SQLRecord = self.data[row]
        return record.values.get(column.name) is None

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        column = self.table.columns[col]

        record: SQLRecord = self.data[row]

        value = record.values.get(column.name)

        if value is None:
            if column.datatype.name == "BOOLEAN":
                return False
            return NULL_DISPLAY

        if not str(value).strip():
            return ''

        if column.datatype.category == DataTypeCategory.TEMPORAL:
            if isinstance(value, datetime.datetime):
                if column.datatype.name == "DATE":
                    return value.strftime("%Y-%m-%d")
                elif column.datatype.name == "TIME":
                    return value.strftime("%H:%M:%S")
                elif column.datatype.name == "DATETIME":
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                elif column.datatype.name == "TIMESTAMP":
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                elif column.datatype.name == "YEAR":
                    return value.strftime("%Y")

            return value

        elif column.datatype.name == "BOOLEAN":
            return bool(value == 1)

        return str(value)

    def SetValueByRow(self, value, row, col):
        column: SQLColumn = self.table.columns[col]

        if value == NULL_DISPLAY or (isinstance(value, str) and not value.strip()):
            value = None

        self.data[row].values[column.name] = value

        return True

    def GetAttr(self, item, col, attr):
        try:
            column: SQLColumn = self.table.columns[col]
        except Exception:
            return False

        row = self.GetRow(item)
        if 0 <= row < len(self.data) and self._is_null(row, col):
            attr.SetItalic(True)
            attr.SetColour(wx.Colour(180, 180, 120))
        else:
            color = column.datatype.category.value.color
            attr.SetColour(wx.Colour(color))

        if column.is_primary_key:
            attr.SetBold(True)

        return True

    def HasValue(self, item, col):
        return bool(self.data)


    def add_row(self, data: SQLRecord) -> wx.dataview.DataViewItem:
        self.data.append(data)
        self.RowAppended()
        return self.GetItem(len(self.data) - 1)


class TableRecordsController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_records: TableRecordsDataViewCtrl):
        self.list_ctrl_records = list_ctrl_records
        self.list_ctrl_records.make_advanced_dialog = self.make_advanced_dialog

        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        CURRENT_SESSION.subscribe(self._load_session)
        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._load_table)
        
        self.executor: Optional[RecordsExecutor] = None

    def _load_session(self, session: Session):
        self.session = session
        self.executor = RecordsExecutor(session) if session else None

    def _load_database(self, database: SQLDatabase):
        self.database = database

    def _load_table(self, table: SQLTable):
        if table is not None:
            self.table = table
            self.load_records_async()

    def _on_auto_apply_changed(self, auto_apply_enabled: bool):
        """Handle auto-apply setting change and update toolbar states."""
        selected_records = self.get_selected_records()
        self._update_toolbar_states(selected_records)

    def load_records_async(self, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None):
        """Load records asynchronously using RecordsExecutor."""
        if not self.executor or not self.table:
            return
            
        self.executor.load_records(
            table=self.table,
            on_complete=self._on_records_loaded,
            filters=filters,
            limit=limit,
            offset=offset,
            orders=orders
        )
    
    def _on_records_loaded(self, result: RecordsOperationResult):
        """Handle completion of records loading."""
        if result.success and result.records is not None:
            self.table.records.set_value(result.records)
            self.load_model()
        else:
            logger.error(f"Failed to load records: {result.error}")
            # Fallback to synchronous loading
            try:
                self.table.load_records()
                self.load_model()
            except Exception as ex:
                logger.error(f"Fallback loading also failed: {ex}", exc_info=True)

    def load_model(self):
        self.model = RecordsModel(self.table, len(self.table.columns))
        self.model.set_observable(self.table.records)
        self.list_ctrl_records.AssociateModel(self.model)

    def _do_edit(self, item, model_column: int = 1):
        column = self.list_ctrl_records.GetColumn(model_column)
        self.list_ctrl_records.edit_item(item, column)

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON RECORD EDITING DONE {'#' * 10}")
        table: SQLTable = CURRENT_TABLE.get_value()

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_record = self.model.data[self.model.GetRow(item)]
        original_record = next((r for r in list(table.records) if r.id == current_record.id), None)

        if current_record.id == -1 or current_record != original_record:
            if AUTO_APPLY.get_value() and current_record.is_valid():
                try:
                    current_record.save()
                except Exception as ex:
                    logger.error(f"Error saving record: {ex}", exc_info=True)
                else:
                    # Refresh records after successful save
                    self.load_records_async()
            else:
                NEW_RECORDS.append(current_record, replace_existing=True)

        event.Skip()

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON SELECTION CHANGED {'#' * 10}")
        selected_records = self.get_selected_records()
        CURRENT_RECORDS.set_value(selected_records)
        
        # Update toolbar states based on selection
        self._update_toolbar_states(selected_records)
        
        event.Skip()


    def _update_toolbar_states(self, selected_records: list):
        """Update toolbar tool states based on record selection and auto-apply setting."""
        # This method provides the logic for toolbar state management
        # The actual toolbar updates will be handled by the main controller
        # through the CURRENT_RECORDS observable subscription
        
        # Calculate toolbar states
        has_selection = len(selected_records) > 0
        has_single_selection = len(selected_records) == 1
        auto_apply_enabled = AUTO_APPLY.get_value()
        
        # Store states for the main controller to use
        self._toolbar_states = {
            'duplicate_enabled': has_single_selection,
            'delete_enabled': has_selection,
            'apply_enabled': not auto_apply_enabled,
            'cancel_enabled': not auto_apply_enabled
        }

    def get_selection_state(self):
        """Return the current selection state for toolbar management."""
        selected_records = self.get_selected_records()
        return {
            'has_selection': len(selected_records) > 0,
            'has_single_selection': len(selected_records) == 1,
            'auto_apply_enabled': AUTO_APPLY.get_value()
        }

    def get_toolbar_states(self):
        """Return the current toolbar states for the main controller."""
        return getattr(self, '_toolbar_states', {
            'duplicate_enabled': False,
            'delete_enabled': False,
            'apply_enabled': not AUTO_APPLY.get_value(),
            'cancel_enabled': not AUTO_APPLY.get_value()
        })

    def make_advanced_dialog(self, parent, value: str):
        dialog = ColumnContentDialogController(parent, value)

        return dialog

    def get_selected_records(self):
        return [self.model.data[self.model.GetRow(row)] for row in self.list_ctrl_records.GetSelections()]

    def get_first_editable_column(self):
        for i, column in enumerate(self.table.columns):
            if not column.is_auto_increment and not column.server_default:
                return i

        return None

    def _do_new_empty_record(self, index: int, copy_from_selected: bool = False, use_server_defaults: bool = True):
        """Helper method to create a new empty record at the specified index."""
        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        values = dict()
        current_record = None

        if copy_from_selected:
            selected = self.list_ctrl_records.GetSelection()
            if selected.IsOk():
                current_record: SQLRecord = self.model.get_data_by_item(selected)

        column_server_default = {}
        for column in table.columns:
            if column.is_auto_increment:
                continue

            if use_server_defaults and column.server_default:
                if not column_server_default.get(column.server_default):
                    if table.database.context.execute(f"SELECT {column.server_default} as column_default"):
                        column_server_default[column.server_default] = table.database.context.fetchone()['column_default']

                values[column.name] = column_server_default[column.server_default]
            elif copy_from_selected and current_record:
                values[column.name] = current_record.values.get(column.name)

        new_empty_record = session.context.build_empty_record(
            table,
            values=values
        )

        table.records.insert(index, new_empty_record)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_records.UnselectAll()
        self.list_ctrl_records.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

    def do_refresh_records(self):
        """Refresh records from database."""
        if self.table:
            self.load_records_async()

    def do_insert_record(self):
        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_records.GetSelection()

        index = len(table.records)
        if selected.IsOk():
            current_record: SQLRecord = self.model.get_data_by_item(selected)
            index = table.records.index(current_record) + 1

        self._do_new_empty_record(index, copy_from_selected=False, use_server_defaults=True)

    def do_duplicate_record(self):
        session = CURRENT_SESSION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_records.GetSelection()

        if not selected.IsOk():
            return

        index = len(table.records)
        if selected.IsOk():
            current_record: SQLRecord = self.model.get_data_by_item(selected)
            index = table.records.index(current_record) + 1

        self._do_new_empty_record(index, copy_from_selected=True, use_server_defaults=False)

    def do_delete_record(self):
        table = CURRENT_TABLE.get_value()

        records = CURRENT_RECORDS.get_value()

        if records:
            try:
                SQLRecord.delete_many(table, records)
                CURRENT_RECORDS.set_value([])
                # Refresh records after successful deletion
                self.load_records_async()
            except Exception as ex:
                logger.error(f"Error deleting records: {ex}", exc_info=True)
                wx.MessageBox(
                    f"Failed to delete records: {ex}",
                    "Error",
                    wx.OK | wx.ICON_ERROR
                )

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
