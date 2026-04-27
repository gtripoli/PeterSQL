import datetime

from typing import Any, Optional
from gettext import gettext as _

import wx
import wx.dataview

from helpers.dataview import BaseDataViewListModel

from structures.session import Session
from structures.engines.datatype import DataTypeCategory, SQLDataType

from windows.components.popup import PopupCalendar, PopupCalendarTime
from windows.components.renders import AdvancedTextRenderer, FloatRenderer, IntegerRenderer, PopupRenderer, TextRenderer, TimeRenderer
from windows.components.dataview import QueryEditorResultsDataViewCtrl

from windows.main.query.executor import ExecutionResult


class _ReadOnlyPopupRenderer(PopupRenderer):
    def ActivateCell(self, rect, model, item, col, mouseEvent):
        return False


class _ReadOnlyTimeRenderer(TimeRenderer):
    def HasEditorCtrl(self):
        return False


class QueryResultsRenderer:
    def __init__(self, notebook: wx.Notebook, session: Session):
        self.notebook = notebook
        self.session = session
        self._models: list[Any] = []
        self._tab_counter = 0

    def create_result_tab(self, result: ExecutionResult) -> wx.Panel:
        self._tab_counter += 1

        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        if result.success and result.columns:
            results_dataview = QueryEditorResultsDataViewCtrl(panel)
            self._populate_grid(results_dataview, result)
            sizer.Add(results_dataview, 1, wx.EXPAND | wx.ALL, 5)

            tab_name = self._generate_tab_name(result)
        elif result.success:
            msg = wx.StaticText(
                panel,
                label=_("{affected_rows} rows affected").format(
                    affected_rows=result.affected_rows or 0
                ),
            )
            msg.SetFont(msg.GetFont().MakeBold())
            sizer.Add(msg, 1, wx.ALIGN_CENTER | wx.ALL, 20)

            tab_name = _("Query {query_number}").format(query_number=self._tab_counter)
        else:
            error_panel = self._create_error_panel(panel, result)
            sizer.Add(error_panel, 1, wx.EXPAND | wx.ALL, 5)

            tab_name = _("Query {query_number} (Error)").format(
                query_number=self._tab_counter
            )

        footer = self._create_footer(panel, result)
        sizer.Add(footer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, tab_name, select=True)

        return panel

    def _generate_tab_name(self, result: ExecutionResult) -> str:
        if result.columns and result.rows is not None:
            return _("Query {query_number} ({rows_count} rows × {columns_count} cols)").format(
                query_number=self._tab_counter,
                rows_count=len(result.rows),
                columns_count=len(result.columns),
            )
        return _("Query {query_number}").format(query_number=self._tab_counter)

    def _get_column_datatype(self, result: ExecutionResult, column_index: int) -> Optional[SQLDataType]:
        if not result.column_datatypes:
            return None

        if column_index >= len(result.column_datatypes):
            return None

        return result.column_datatypes[column_index]

    def _get_column_renderer(
            self,
            results_dataview: QueryEditorResultsDataViewCtrl,
            datatype: Optional[SQLDataType]
    ) -> wx.dataview.DataViewRenderer:
        if datatype is None:
            return TextRenderer(mode=wx.dataview.DATAVIEW_CELL_INERT)

        if datatype.name == "BOOLEAN":
            return wx.dataview.DataViewToggleRenderer(
                mode=wx.dataview.DATAVIEW_CELL_INERT,
                align=wx.ALIGN_CENTER,
            )

        if datatype.name == "DATE":
            return _ReadOnlyPopupRenderer(PopupCalendar)

        if datatype.name == "TIME":
            return _ReadOnlyTimeRenderer()

        if datatype.name in ["DATETIME", "TIMESTAMP"]:
            return _ReadOnlyPopupRenderer(PopupCalendarTime)

        if datatype.category == DataTypeCategory.INTEGER:
            return IntegerRenderer(mode=wx.dataview.DATAVIEW_CELL_INERT)

        if datatype.category == DataTypeCategory.REAL:
            return FloatRenderer(mode=wx.dataview.DATAVIEW_CELL_INERT)

        if datatype.category == DataTypeCategory.TEXT:
            return AdvancedTextRenderer(
                mode=wx.dataview.DATAVIEW_CELL_INERT,
                dialog_factory=results_dataview.make_advanced_dialog,
            )

        return TextRenderer(mode=wx.dataview.DATAVIEW_CELL_INERT)

    def _populate_grid(
            self,
            results_dataview: QueryEditorResultsDataViewCtrl,
            result: ExecutionResult
    ) -> None:
        if not result.columns:
            return

        for i, col_name in enumerate(result.columns):
            datatype = self._get_column_datatype(result, i)
            renderer = self._get_column_renderer(results_dataview, datatype)
            align = wx.ALIGN_CENTER if datatype and datatype.name == "BOOLEAN" else wx.ALIGN_LEFT

            column = wx.dataview.DataViewColumn(
                col_name,
                renderer,
                i,
                width=results_dataview.measure_text(col_name),
                align=align,
                flags=wx.dataview.DATAVIEW_COL_RESIZABLE,
            )
            results_dataview.AppendColumn(column)

        model = QueryResultsModel(column_count=len(result.columns))
        model.load(result.rows, result.columns, result.column_datatypes)
        self._models.append(model)
        results_dataview.AssociateModel(model)
        wx.CallAfter(results_dataview.autosize_columns_from_content)

    def _create_footer(self, parent: wx.Panel, result: ExecutionResult) -> wx.StaticText:
        parts = []

        if result.affected_rows is not None:
            parts.append(_("{rows_count} rows").format(rows_count=result.affected_rows))

        parts.append(_("{elapsed_ms:.1f} ms").format(elapsed_ms=result.elapsed_ms))

        if result.warnings:
            parts.append(
                _("{warnings_count} warnings").format(
                    warnings_count=len(result.warnings)
                )
            )

        footer_text = " | ".join(parts)
        footer = wx.StaticText(parent, label=footer_text)
        footer.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        return footer

    def _create_error_panel(self, parent: wx.Panel, result: ExecutionResult) -> wx.Panel:
        error_panel = wx.Panel(parent)
        error_sizer = wx.BoxSizer(wx.VERTICAL)

        error_label = wx.StaticText(error_panel, label=_("Error:"))
        error_label.SetFont(error_label.GetFont().MakeBold())
        error_sizer.Add(error_label, 0, wx.ALL, 5)

        error_text = wx.TextCtrl(
            error_panel,
            value=result.error or _("Unknown error"),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        error_text.SetBackgroundColour(wx.Colour(255, 240, 240))
        error_sizer.Add(error_text, 1, wx.EXPAND | wx.ALL, 5)

        error_panel.SetSizer(error_sizer)
        return error_panel

    def clear_all_tabs(self) -> None:
        while self.notebook.GetPageCount() > 0:
            self.notebook.DeletePage(0)
        self._models = []
        self._tab_counter = 0


class QueryResultsModel(BaseDataViewListModel):
    def __init__(self, column_count: int):
        super().__init__(column_count)
        self._columns: list[str] = []
        self._column_datatypes: list[Optional[SQLDataType]] = []

    def load(
            self,
            data: list[Any],
            columns: list[str],
            column_datatypes: Optional[list[Optional[SQLDataType]]] = None,
    ):
        self._columns = columns
        self._column_datatypes = column_datatypes or [None for _ in columns]
        BaseDataViewListModel.load(self, data)

    def GetValueByRow(self, row, col):
        if row < 0 or row >= len(self.data):
            return ""

        if col < 0 or col >= len(self._columns):
            return ""

        value = self._get_cell_value(self.data[row], col)
        if value is None:
            return ""

        datatype = self._get_column_datatype(col)
        if datatype is None:
            return str(value)

        if datatype.name == "BOOLEAN":
            return bool(value)

        if datatype.category == DataTypeCategory.TEMPORAL:
            return self._format_temporal_value(value, datatype.name)

        return str(value)

    def SetValueByRow(self, value, row, col):
        return False

    def HasValue(self, item, col):
        if col < 0 or col >= len(self._columns):
            return False

        row = self.GetRow(item)
        if row < 0 or row >= len(self.data):
            return False

        return self._get_cell_value(self.data[row], col) is not None

    def GetAttr(self, item, col, attr):
        datatype = self._get_column_datatype(col)
        if datatype is None:
            return super().GetAttr(item, col, attr)

        color = datatype.category.value.color
        attr.SetColour(wx.Colour(color))
        return super().GetAttr(item, col, attr)

    def _get_cell_value(self, row_data: Any, col: int) -> Any:
        if isinstance(row_data, dict):
            return row_data.get(self._columns[col])

        if col < len(row_data):
            return row_data[col]

        return None

    def _get_column_datatype(self, col: int) -> Optional[SQLDataType]:
        if col < 0 or col >= len(self._column_datatypes):
            return None

        return self._column_datatypes[col]

    def _format_temporal_value(self, value: Any, datatype_name: str) -> str:
        if isinstance(value, datetime.datetime):
            if datatype_name == "DATE":
                return value.strftime("%Y-%m-%d")

            if datatype_name == "TIME":
                return value.strftime("%H:%M:%S")

            if datatype_name in ["DATETIME", "TIMESTAMP"]:
                return value.strftime("%Y-%m-%d %H:%M:%S")

            if datatype_name == "YEAR":
                return value.strftime("%Y")

        if isinstance(value, datetime.date) and datatype_name == "DATE":
            return value.strftime("%Y-%m-%d")

        if isinstance(value, datetime.time) and datatype_name == "TIME":
            return value.strftime("%H:%M:%S")

        return str(value)
