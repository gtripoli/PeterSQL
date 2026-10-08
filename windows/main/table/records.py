import datetime
import re

from gettext import gettext as _
from typing import Optional, Any

import wx
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

# ---------------------------------------------------------------------------
# Module-level constants used by RecordsModel.is_static_default
# ---------------------------------------------------------------------------

# Sentinel used by RecordsModel.get_static_default to distinguish a cached
# value of None (or 0, '') from "not in cache".
_STATIC_DEFAULT_SENTINEL: Any = object()

# Whitelist regex for SQL default expressions that are provably constant.
# Anything not matching is treated as dynamic (evaluated every time, never
# cached).  The list is intentionally narrow to stay conservative:
#   - NULL literal
#   - Boolean literals  TRUE / FALSE
#   - Integer or float numeric literals (optionally negative)
#   - SQL single-quoted string literals (supports '' escaping)
_STATIC_DEFAULT_RE = re.compile(
    r"^(?:"
    r"NULL"              # NULL keyword
    r"|TRUE|FALSE"       # boolean keywords
    r"|-?\d+(\.\d+)?"   # integer or decimal literal
    r"|'(?:[^']|'')*'"  # SQL single-quoted string ('' = escaped quote)
    r")$",
    re.IGNORECASE,
)


class RecordsModel(BaseObservableDataViewListModel):
    def __init__(self, table: SQLTable, column_count: Optional[int] = None):
        super().__init__(column_count)

        self.table: SQLTable = table

        # Cache for server-side defaults that are provably constant (NULL,
        # numeric literals, simple string literals, TRUE/FALSE).  The cache
        # lives with the model, so it is cleared automatically whenever a new
        # table is loaded (which recreates the model via load_model_for).
        # Key: (column_name, original server_default expression)
        # Value: the Python value returned by the DB engine the first time the
        #        expression was evaluated.
        self._static_defaults_cache: dict[tuple[str, str], Any] = {}

    def _load(self, data):
        super()._load(data)

    def _is_null(self, row, col):
        column = self.table.columns[col]
        record: SQLRecord = self.data[row]
        return record.values.get(column.name) is None

    def GetValueByRow(self, row, col):
        if not len(self.data):
            return None

        if col < 0:
            logger.error(f"Invalid record column index: {col}")
            return ""

        try:
            column = self.table.columns[col]
        except IndexError:
            logger.error(f"Invalid record column index: {col}")
            return ""

        record: SQLRecord = self.data[row]

        value = record.values.get(column.name)

        if value is None:
            # if column.datatype.name == "BOOLEAN":
            #     return False
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
            attr.SetColour(wx.Colour(*color))

        if column.is_primary_key:
            attr.SetBold(True)

        return True

    def HasValue(self, item, col):
        return bool(self.data)

    # ------------------------------------------------------------------
    # Static-default cache helpers
    # ------------------------------------------------------------------

    def get_static_default(self, col_name: str, server_default: str) -> tuple[bool, Any]:
        """Return ``(found, value)`` for a static default.

        ``found`` is True even when the cached value is falsy (0, '', None).
        Callers must use the boolean flag rather than truthiness of *value*.
        """
        key = (col_name, server_default)
        value = self._static_defaults_cache.get(key, _STATIC_DEFAULT_SENTINEL)
        if value is _STATIC_DEFAULT_SENTINEL:
            return False, None
        return True, value

    def set_static_default(self, col_name: str, server_default: str, value: Any) -> None:
        """Store a materialised static default value in the cache."""
        self._static_defaults_cache[(col_name, server_default)] = value

    def clear_static_defaults_cache(self) -> None:
        """Discard all cached static default values.

        The cache is cleared implicitly whenever a new table is loaded because
        ``TableRecordsController.load_model_for`` always creates a fresh
        ``RecordsModel`` instance (and therefore a fresh empty
        ``_static_defaults_cache``).

        This method exposes the same invalidation explicitly so callers can
        force a reset when DDL or column metadata changes without recreating
        the entire model.
        """
        self._static_defaults_cache.clear()

    @staticmethod
    def is_static_default(expr: str) -> bool:
        """Return True only for known-static SQL default expressions.

        Conservative: if the expression is not in the whitelist it returns
        False so the caller evaluates it on every new record without caching
        (dynamic path).  Examples of dynamic expressions: ``NOW()``,
        ``uuid()``, ``CURRENT_DATE``, ``WEEK(CURRENT_TIMESTAMP())``.
        """
        return bool(_STATIC_DEFAULT_RE.match(expr.strip()))

    def add_row(self, data: SQLRecord) -> wx.dataview.DataViewItem:
        self.data.append(data)
        self.RowAppended()
        return self.GetItem(len(self.data) - 1)


class TableRecordsController:
    app = wx.GetApp()
    executor: Optional[RecordsExecutor] = None
    def __init__(self, list_ctrl_records: TableRecordsDataViewCtrl):
        self.list_ctrl_records = list_ctrl_records
        self.list_ctrl_records.make_advanced_dialog = self.make_advanced_dialog

        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self._on_selection_changed)
        self.list_ctrl_records.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self._on_item_value_changed)

        CURRENT_SESSION.subscribe(self._load_session)
        CURRENT_DATABASE.subscribe(self._load_database)
        CURRENT_TABLE.subscribe(self._load_table)
        
    def _load_session(self, session: Session):
        self.session = session
        self.executor = RecordsExecutor(session) if session else None

    def _load_database(self, database: SQLDatabase):
        self.database = database

    def _load_table(self, table: SQLTable):
        self.table = table

    def _on_auto_apply_changed(self, auto_apply_enabled: bool):
        """Handle auto-apply setting change and update toolbar states."""
        selected_records = self.get_selected_records()
        self._update_toolbar_states(selected_records)

    def load_records_async(self, obj=None, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None):
        """Load records asynchronously using RecordsExecutor."""
        target = obj or self.table
        if not self.executor or not target:
            return

        self.executor.load_records(
            table=target,
            on_complete=lambda result: self._on_records_loaded(result, target),
            filters=filters,
            limit=limit,
            offset=offset,
            orders=orders
        )

    def _on_records_loaded(self, result: RecordsOperationResult, obj=None):
        """Handle completion of records loading."""
        target = obj or self.table
        if result.success and result.records is not None:
            target.records.set_value(result.records)
        else:
            logger.error(f"Failed to load records: {result.error}")
            try:
                target.load_records()
            except Exception as ex:
                logger.error(f"Fallback loading also failed: {ex}", exc_info=True)

    def load_model_for(self, obj):
        # A new RecordsModel is created for every table load, which implicitly
        # clears the static-default cache (fresh _static_defaults_cache dict).
        # DDL changes always end up here via:
        #   do_apply_table → CURRENT_TABLE.set_value → _on_current_table
        #   → _load_records_page → load_model_for
        # so stale cached defaults can never survive a DDL change.
        self.model = RecordsModel(obj, len(obj.columns))
        self.model.set_observable(obj.records)
        self.list_ctrl_records.AssociateModel(self.model)

    def load_model(self):
        self.load_model_for(self.table)

    def _do_edit(self, item, model_column: int = 1):
        column = self.list_ctrl_records.GetColumn(model_column)
        self.list_ctrl_records.edit_item(item, column)

    def _on_item_value_changed(self, event: wx.dataview.DataViewEvent):
        logger.debug(f"{'#' * 10} ON RECORD EDITING DONE {'#' * 10}")

        item = event.GetItem()

        if not item.IsOk():
            event.Skip()
            return

        current_record = self.model.data[self.model.GetRow(item)]

        if AUTO_APPLY.get_value() and current_record.is_valid():
            try:
                current_record.save()
            except Exception as ex:
                logger.error(f"Error saving record: {ex}", exc_info=True)
            else:
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

        values: dict = {}
        current_record = None

        if copy_from_selected:
            selected = self.list_ctrl_records.GetSelection()
            if selected.IsOk():
                current_record: SQLRecord = self.model.get_data_by_item(selected)

        if use_server_defaults:
            context = table.database.context

            # Columns whose server-default value still needs to be fetched from
            # the DB engine (either dynamic, or a static that is not yet cached).
            needs_eval: list = []

            for column in table.columns:
                if column.is_auto_increment or not column.server_default:
                    continue

                expr = column.server_default

                if RecordsModel.is_static_default(expr):
                    found, cached_value = self.model.get_static_default(column.name, expr)
                    if found:
                        # Serve directly from the model cache — no DB round-trip.
                        values[column.name] = cached_value
                        continue

                # Dynamic, or a static that is not yet cached → schedule evaluation.
                needs_eval.append(column)

            if needs_eval:
                # Build a single SELECT that evaluates all required expressions.
                # Use the column name (quoted via quote_identifier) as the SQL
                # alias so the result row can be addressed by column.name.
                parts = [
                    f"{col.server_default} AS {context.quote_identifier(col.name)}"
                    for col in needs_eval
                ]
                sql = f"SELECT {', '.join(parts)}"
                if context.execute(sql):
                    row = context.fetchone()
                    if row:
                        for col in needs_eval:
                            # Use 'col.name' as dict key (drivers strip alias quoting).
                            evaluated = row[col.name]
                            values[col.name] = evaluated
                            # Persist only static defaults in the model cache.
                            if RecordsModel.is_static_default(col.server_default):
                                self.model.set_static_default(col.name, col.server_default, evaluated)

        for column in table.columns:
            if column.is_auto_increment:
                continue
            if use_server_defaults and column.server_default and column.name in values:
                # Already handled in the server-defaults block above.
                continue
            if copy_from_selected and current_record:
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

    def do_apply_records(self):
        """Save all pending records from NEW_RECORDS."""
        records = list(NEW_RECORDS)
        if not records:
            return

        errors = []
        for record in records:
            try:
                record.save()
            except Exception as ex:
                logger.error(f"Error saving record: {ex}", exc_info=True)
                errors.append(str(ex))

        NEW_RECORDS.clear()

        if errors:
            wx.MessageBox(
                "\n".join(errors),
                _("Error saving records"),
                wx.OK | wx.ICON_ERROR,
            )

        self.load_records_async()

    def do_cancel_records(self):
        """Discard all pending changes in NEW_RECORDS."""
        # BUG FIX: was load_model() which recreates the model from in-memory table.records
        # (already modified by SetValueByRow), so edits were never actually discarded.
        # load_records_async() fetches fresh data from the DB, properly reversing edits.
        NEW_RECORDS.clear()
        if self.table:
            self.load_records_async()

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
