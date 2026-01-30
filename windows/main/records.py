import datetime
from typing import Optional

import wx.dataview

from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel
from helpers.observables import ObservableList

from structures.connection import Connection
from structures.engines.database import SQLTable, SQLDatabase, SQLColumn, SQLRecord
from structures.engines.datatype import DataTypeCategory

from windows import TableRecordsDataViewCtrl, AdvancedCellEditorDialog
from windows.components.stc.profiles import syntaxRegistry, detect_syntax_id
from windows.components.stc.styles import apply_stc_theme
from windows.components.stc.syntax import SyntaxProfile
from windows.main import CURRENT_TABLE, CURRENT_CONNECTION, CURRENT_DATABASE, AUTO_APPLY, CURRENT_RECORDS

NEW_RECORDS: ObservableList[SQLRecord] = ObservableList()


class RecordsModel(BaseDataViewListModel):
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
            if isinstance(value, datetime.datetime) :
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
        self.list_ctrl_records.make_advanced_dialog = self.make_advanced_dialog

        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        CURRENT_CONNECTION.subscribe(self._load_session)
        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Connection):
        self.session = session

    def _load_database(self, database: SQLDatabase):
        self.database = database

    def _load_table(self, table: SQLTable):
        if table is not None:
            self.table = table

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
                    records = list(self.session.context.get_records(table=self.table))

                self.table.records.set_value(records)
            else:
                NEW_RECORDS.append(current_record, replace_existing=True)

        event.Skip()

    def _on_selection_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON SELECTION CHANGED {'#' * 10}")
        CURRENT_RECORDS.set_value(self.get_selected_records())
        event.Skip()

    def make_advanced_dialog(self, parent, value: str):
        dialog = AdvancedCellEditorController(parent, value)
        

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
        session = CURRENT_CONNECTION.get_value()
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
            table=table,
            values=values
        )

        table.records.insert(index, new_empty_record)

        new_empty_item = self.model.GetItem(index)

        self.list_ctrl_records.UnselectAll()
        self.list_ctrl_records.Select(new_empty_item)

        self._do_edit(new_empty_item, 1)

    def do_insert_record(self):
        session = CURRENT_CONNECTION.get_value()
        table = CURRENT_TABLE.get_value()

        selected = self.list_ctrl_records.GetSelection()

        index = len(table.records)
        if selected.IsOk():
            current_record: SQLRecord = self.model.get_data_by_item(selected)
            index = table.records.index(current_record) + 1

        self._do_new_empty_record(index, copy_from_selected=False, use_server_defaults=True)

    def do_duplicate_record(self):
        session = CURRENT_CONNECTION.get_value()
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

        SQLRecord.delete_many(table, records)

        CURRENT_RECORDS.set_value([])

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


class AdvancedCellEditorController(AdvancedCellEditorDialog):
    app = wx.GetApp()

    def __init__(self, parent, value: str):
        super().__init__(parent)

        self.syntax_registry = syntaxRegistry

        self.syntax_choice.AppendItems(self.syntax_registry.labels())
        self.advanced_stc_editor.SetText(value or "")
        self.advanced_stc_editor.EmptyUndoBuffer()

        self.app.theme_manager.register(self.advanced_stc_editor, self._get_current_syntax_profile)

        self.syntax_choice.SetStringSelection(self._auto_syntax_profile().label)

        self.do_apply_syntax(do_format=True)

    def _auto_syntax_profile(self) -> SyntaxProfile:
        text = self.advanced_stc_editor.GetText()

        syntax_id = detect_syntax_id(text)
        return self.syntax_registry.get(syntax_id)

    def _get_current_syntax_profile(self) -> SyntaxProfile:
        label = self.syntax_choice.GetStringSelection()
        # text = self.advanced_stc_editor.GetText()
        #
        # syntax_id = detect_syntax_id(text)
        return self.syntax_registry.get(label)

    def on_syntax_changed(self, _evt):
        label = self.syntax_choice.GetStringSelection()
        self.do_apply_syntax(label)

    def do_apply_syntax(self, do_format: bool = True):
        label = self.syntax_choice.GetStringSelection()
        syntax_profile = self.syntax_registry.by_label(label)

        apply_stc_theme(self.advanced_stc_editor, syntax_profile)

        if do_format and syntax_profile.formatter:
            old = self.advanced_stc_editor.GetText()
            try:
                formatted = syntax_profile.formatter(old)
            except Exception:
                return

            if formatted != old:
                self._replace_text_undo_friendly(formatted)

    def _replace_text_undo_friendly(self, new_text: str):
        self.advanced_stc_editor.BeginUndoAction()
        try:
            self.advanced_stc_editor.SetText(new_text)
        finally:
            self.advanced_stc_editor.EndUndoAction()
