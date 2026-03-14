import contextlib
import dataclasses
import datetime
import enum
import threading
import time

from typing import Any, Callable, Optional
from gettext import gettext as _

import wx
import wx.dataview

from helpers.logger import logger
from helpers.dataview import BaseDataViewListModel

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.engines.datatype import DataTypeCategory, SQLDataType

from windows.components.popup import PopupCalendar, PopupCalendarTime
from windows.components.renders import AdvancedTextRenderer, FloatRenderer, IntegerRenderer, PopupRenderer, TextRenderer, TimeRenderer
from windows.components.dataview import QueryEditorResultsDataViewCtrl


class _ReadOnlyPopupRenderer(PopupRenderer):
    def ActivateCell(self, rect, model, item, col, mouseEvent):
        return False


class _ReadOnlyTimeRenderer(TimeRenderer):
    def HasEditorCtrl(self):
        return False


@dataclasses.dataclass
class ParsedStatement:
    text: str
    start_pos: int
    end_pos: int
    statement_index: int


@dataclasses.dataclass
class ExecutionResult:
    statement: ParsedStatement
    success: bool
    columns: Optional[list[str]] = None
    rows: Optional[list[tuple]] = None
    column_datatypes: Optional[list[Optional[SQLDataType]]] = None
    affected_rows: Optional[int] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    cancelled: bool = False
    warnings: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ExecutionSummary:
    total_statements: int = 0
    completed_statements: int = 0
    successful_statements: int = 0
    failed_statements: int = 0
    elapsed_ms: float = 0.0
    cancelled: bool = False
    last_statement: Optional[ParsedStatement] = None


class ExecutionMode(enum.Enum):
    ALL = "all"
    SELECTION = "selection"
    CURRENT = "current"


class SQLStatementParser:
    def __init__(self, engine: ConnectionEngine):
        self.engine = engine

    def parse(self, sql_text: str) -> list[ParsedStatement]:
        if not sql_text.strip():
            return []

        statements = []
        statement_index = 0
        current_start = 0
        i = 0
        length = len(sql_text)

        in_single_quote = False
        in_double_quote = False
        in_line_comment = False
        in_block_comment = False

        while i < length:
            char = sql_text[i]

            if in_line_comment:
                if char == '\n':
                    in_line_comment = False
                i += 1
                continue

            if in_block_comment:
                if i + 1 < length and sql_text[i:i + 2] == '*/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue

            if not in_single_quote and not in_double_quote:
                if self._is_line_comment_start(sql_text, i):
                    in_line_comment = True
                    i += 2
                    continue

                if self._is_block_comment_start(sql_text, i):
                    in_block_comment = True
                    i += 2
                    continue

            if char == "'" and not in_double_quote:
                if i + 1 < length and sql_text[i + 1] == "'":
                    i += 2
                    continue
                in_single_quote = not in_single_quote

            elif char == '"' and not in_single_quote:
                if i + 1 < length and sql_text[i + 1] == '"':
                    i += 2
                    continue
                in_double_quote = not in_double_quote

            elif char == ';' and not in_single_quote and not in_double_quote:
                statement_text = sql_text[current_start:i].strip()
                if statement_text:
                    statements.append(ParsedStatement(
                        text=statement_text,
                        start_pos=current_start,
                        end_pos=i,
                        statement_index=statement_index
                    ))
                    statement_index += 1
                current_start = i + 1

            i += 1

        final_statement = sql_text[current_start:].strip()
        if final_statement:
            statements.append(ParsedStatement(
                text=final_statement,
                start_pos=current_start,
                end_pos=length,
                statement_index=statement_index
            ))

        return statements

    def _is_line_comment_start(self, text: str, pos: int) -> bool:
        if pos + 1 >= len(text):
            return False
        return text[pos:pos + 2] in ('--', '# ')

    def _is_block_comment_start(self, text: str, pos: int) -> bool:
        if pos + 1 >= len(text):
            return False
        return text[pos:pos + 2] == '/*'


class StatementSelector:
    def __init__(self, stc_editor: wx.stc.StyledTextCtrl):
        self.editor = stc_editor

    def get_execution_scope(
            self,
            statements: list[ParsedStatement]
    ) -> tuple[ExecutionMode, list[ParsedStatement]]:
        selection_start = self.editor.GetSelectionStart()
        selection_end = self.editor.GetSelectionEnd()

        if selection_start != selection_end:
            selected_text = self.editor.GetSelectedText().strip()
            if selected_text:
                return (ExecutionMode.SELECTION, [ParsedStatement(
                    text=selected_text,
                    start_pos=selection_start,
                    end_pos=selection_end,
                    statement_index=0
                )])

        caret_pos = self.editor.GetCurrentPos()
        current_stmt = self._find_statement_at_caret(caret_pos, statements)

        if current_stmt:
            return (ExecutionMode.CURRENT, [current_stmt])

        return (ExecutionMode.ALL, statements)

    def _find_statement_at_caret(
            self,
            caret_pos: int,
            statements: list[ParsedStatement]
    ) -> Optional[ParsedStatement]:
        for stmt in statements:
            if stmt.start_pos <= caret_pos <= stmt.end_pos:
                return stmt

        # Caret is in whitespace: execute next statement
        for stmt in statements:
            if caret_pos < stmt.start_pos:
                return stmt

        # Caret after all statements: execute last
        if statements:
            return statements[-1]

        return None


class QueryExecutor:
    def __init__(self, session: Session):
        self.session = session
        self._cancel_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._worker_context: Optional[Any] = None
        self._lock = threading.Lock()

    def execute_statements(
            self,
            statements: list[ParsedStatement],
            on_statement_complete: Callable[[ExecutionResult], None],
            on_all_complete: Callable[[ExecutionSummary], None],
            current_database: Optional[Any] = None,
            stop_on_error: bool = True
    ) -> None:
        self._cancel_requested = False

        self._current_thread = threading.Thread(
            target=self._execute_worker,
            args=(
                statements,
                on_statement_complete,
                on_all_complete,
                current_database,
                stop_on_error,
            ),
            daemon=True
        )
        self._current_thread.start()

    def _execute_worker(
            self,
            statements: list[ParsedStatement],
            on_statement_complete: Callable[[ExecutionResult], None],
            on_all_complete: Callable[[ExecutionSummary], None],
            current_database: Optional[Any],
            stop_on_error: bool
    ) -> None:
        time_start = time.perf_counter()
        summary = ExecutionSummary(total_statements=len(statements))

        try:
            context = self._create_worker_context(current_database)
            self._set_worker_context(context)

            for stmt in statements:
                if self._cancel_requested:
                    summary.cancelled = True
                    break

                summary.last_statement = stmt
                result = self._execute_single(context, stmt)

                if result.success:
                    summary.completed_statements += 1
                    summary.successful_statements += 1
                elif not result.cancelled:
                    summary.completed_statements += 1
                    summary.failed_statements += 1

                self._dispatch_statement_result(on_statement_complete, result)

                if not result.success and stop_on_error:
                    break

        except Exception as ex:
            logger.error(f"Execution worker error: {ex}", exc_info=True)
        finally:
            summary.cancelled = summary.cancelled or self._cancel_requested
            summary.elapsed_ms = (time.perf_counter() - time_start) * 1000

            self._clear_worker_context()

            wx.CallAfter(on_all_complete, summary)

    def _dispatch_statement_result(
            self,
            on_statement_complete: Callable[[ExecutionResult], None],
            result: ExecutionResult,
    ) -> None:
        ui_done_event = threading.Event()

        def _on_ui_thread() -> None:
            on_statement_complete(result)
            ui_done_event.set()

        wx.CallAfter(_on_ui_thread)
        while not ui_done_event.wait(0.05):
            continue

    def _execute_single(self, context: Any, statement: ParsedStatement) -> ExecutionResult:
        start_time = time.time()

        try:
            context.execute(statement.text)

            elapsed_ms = (time.time() - start_time) * 1000

            cursor = context.cursor
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                column_datatypes = context.get_result_column_datatypes(cursor)
                rows = context.fetchall()

                return ExecutionResult(
                    statement=statement,
                    success=True,
                    columns=columns,
                    rows=rows,
                    column_datatypes=column_datatypes,
                    affected_rows=len(rows),
                    elapsed_ms=elapsed_ms
                )
            else:
                affected = cursor.rowcount if cursor.rowcount >= 0 else 0

                return ExecutionResult(
                    statement=statement,
                    success=True,
                    affected_rows=affected,
                    elapsed_ms=elapsed_ms
                )

        except Exception as ex:
            elapsed_ms = (time.time() - start_time) * 1000
            is_cancelled = self._cancel_requested

            return ExecutionResult(
                statement=statement,
                success=False,
                error=str(ex),
                cancelled=is_cancelled,
                elapsed_ms=elapsed_ms
            )

    def _build_worker_connection(self) -> Connection:
        connection = self.session.connection.copy()

        if not connection.has_enabled_tunnel():
            return connection

        context = getattr(self.session, "context", None)
        configuration = getattr(connection, "configuration", None)

        if context is not None and configuration is not None and hasattr(configuration, "_replace"):
            replace_kwargs = {}

            if hasattr(configuration, "hostname") and getattr(context, "host", None):
                replace_kwargs["hostname"] = context.host

            if hasattr(configuration, "port") and getattr(context, "port", None) is not None:
                replace_kwargs["port"] = int(context.port)

            if replace_kwargs:
                connection.configuration = configuration._replace(**replace_kwargs)

        connection.ssh_tunnel = None
        return connection

    def _create_worker_context(self, current_database: Optional[Any]) -> Any:
        context = self.session._get_context_class()(self._build_worker_connection())
        context.connect()

        if current_database is not None:
            with contextlib.suppress(Exception):
                context.set_database(current_database)

        return context

    def _set_worker_context(self, context: Any) -> None:
        with self._lock:
            self._worker_context = context

    def _clear_worker_context(self) -> None:
        context = None

        with self._lock:
            context = self._worker_context
            self._worker_context = None

        if context is not None:
            with contextlib.suppress(Exception):
                context.disconnect()

    def cancel(self) -> None:
        self._cancel_requested = True
        self._clear_worker_context()

    def is_running(self) -> bool:
        return self._current_thread is not None and self._current_thread.is_alive()


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


class QueryEditorController:
    def __init__(
            self,
            stc_editor: wx.stc.StyledTextCtrl,
            results_notebook: wx.Notebook,
            session_provider: Callable[[], Optional[Session]],
            database_provider: Optional[Callable[[], Optional[Any]]] = None,
            cancel_button: Optional[wx.Button] = None,
    ):
        self.editor = stc_editor
        self.notebook = results_notebook
        self.get_session = session_provider
        self.get_database = database_provider or (lambda: None)
        self.cancel_button = cancel_button

        self.parser: Optional[SQLStatementParser] = None
        self.selector = StatementSelector(stc_editor)
        self.executor: Optional[QueryExecutor] = None
        self.renderer: Optional[QueryResultsRenderer] = None
        self._cancel_feedback_pending = False

        self._bind_shortcuts()

    def _bind_shortcuts(self) -> None:
        self.editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        key_code = event.GetKeyCode()
        ctrl_down = event.ControlDown()
        shift_down = event.ShiftDown()

        if key_code == wx.WXK_F5:
            if shift_down:
                self.cancel_execution(event)
            else:
                self.execute_all(event)
            return

        if ctrl_down and key_code == wx.WXK_RETURN:
            self.execute_current(event)
            return

        if ctrl_down and shift_down and key_code == ord('C'):
            self.cancel_execution(event)
            return

        event.Skip()

    def execute_all(self, event: wx.Event) -> None:
        self._execute(ExecutionMode.ALL)

    def execute_current(self, event: wx.Event) -> None:
        self._execute(ExecutionMode.CURRENT)

    def cancel_execution(self, event: wx.Event) -> None:
        if self.executor and self.executor.is_running():
            self._cancel_feedback_pending = True
            self.executor.cancel()
            logger.info("Query execution cancelled")

    def _execute(self, mode: ExecutionMode) -> None:
        session = self.get_session()
        if not session or not session.is_connected:
            wx.MessageBox(
                _("No active database connection"),
                _("Error"),
                wx.OK | wx.ICON_ERROR
            )
            return

        if not self.parser or self.parser.engine != session.engine:
            self.parser = SQLStatementParser(session.engine)
            self.executor = QueryExecutor(session)
            self.renderer = QueryResultsRenderer(self.notebook, session)

        sql_text = self.editor.GetText()
        if not sql_text.strip():
            return

        statements = self.parser.parse(sql_text)
        if not statements:
            return

        if mode == ExecutionMode.CURRENT or mode == ExecutionMode.SELECTION:
            _, statements_to_execute = self.selector.get_execution_scope(statements)
        else:
            statements_to_execute = statements

        if not statements_to_execute:
            return

        self.renderer.clear_all_tabs()
        self._cancel_feedback_pending = False
        self._set_cancel_button_enabled(True)

        self.executor.execute_statements(
            statements=statements_to_execute,
            on_statement_complete=self._on_statement_complete,
            on_all_complete=self._on_all_complete,
            current_database=self.get_database(),
            stop_on_error=True
        )

    def _on_statement_complete(self, result: ExecutionResult) -> None:
        if result.cancelled:
            return

        if self.renderer:
            self.renderer.create_result_tab(result)

    def _set_cancel_button_enabled(self, enabled: bool) -> None:
        if self.cancel_button is not None:
            self.cancel_button.Enable(enabled)

    def _format_elapsed(self, elapsed_ms: float) -> str:
        if elapsed_ms < 1000:
            return _("{elapsed_ms:.0f} ms").format(elapsed_ms=elapsed_ms)

        return _("{elapsed_s:.2f} s").format(elapsed_s=elapsed_ms / 1000)

    def _show_cancel_message(self, summary: ExecutionSummary) -> None:
        last_statement_label = _("none")
        if summary.last_statement is not None:
            last_statement_label = str(summary.last_statement.statement_index + 1)

        wx.MessageBox(
            _(
                "Query execution stopped after {elapsed}.\n"
                "Completed statements: {completed}/{total}.\n"
                "Successful: {success}.\n"
                "Failed: {failed}.\n"
                "Last statement: #{last}."
            ).format(
                elapsed=self._format_elapsed(summary.elapsed_ms),
                completed=summary.completed_statements,
                total=summary.total_statements,
                success=summary.successful_statements,
                failed=summary.failed_statements,
                last=last_statement_label,
            ),
            _("Query execution cancelled"),
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_all_complete(self, summary: ExecutionSummary) -> None:
        self._set_cancel_button_enabled(False)

        if summary.cancelled and self._cancel_feedback_pending:
            self._show_cancel_message(summary)

        self._cancel_feedback_pending = False
        logger.info("Query execution completed")


class QueryResultsController(QueryEditorController):
    def __init__(
            self,
            stc_sql_query: wx.stc.StyledTextCtrl,
            notebook_sql_results: wx.Notebook,
            cancel_button: Optional[wx.Button] = None,
    ):
        from windows.main import CURRENT_DATABASE, CURRENT_SESSION  # Lazy import: unavoidable circular dependency.

        super().__init__(
            stc_editor=stc_sql_query,
            results_notebook=notebook_sql_results,
            session_provider=lambda: CURRENT_SESSION.get_value(),
            database_provider=lambda: CURRENT_DATABASE.get_value(),
            cancel_button=cancel_button,
        )
