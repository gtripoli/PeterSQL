import dataclasses
import enum
import threading
import time

from typing import Any, Callable, Optional
from gettext import gettext as _

import wx
import wx.dataview

from helpers.logger import logger

from structures.session import Session
from structures.connection import ConnectionEngine

from windows.components.dataview import QueryEditorResultsDataViewCtrl


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
    affected_rows: Optional[int] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    warnings: list[str] = dataclasses.field(default_factory=list)


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
                if i + 1 < length and sql_text[i:i+2] == '*/':
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
                if i + 1 < length and sql_text[i+1] == "'":
                    i += 2
                    continue
                in_single_quote = not in_single_quote

            elif char == '"' and not in_single_quote:
                if i + 1 < length and sql_text[i+1] == '"':
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
        return text[pos:pos+2] in ('--', '# ')

    def _is_block_comment_start(self, text: str, pos: int) -> bool:
        if pos + 1 >= len(text):
            return False
        return text[pos:pos+2] == '/*'


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
        self._lock = threading.Lock()

    def execute_statements(
        self,
        statements: list[ParsedStatement],
        on_statement_complete: Callable[[ExecutionResult], None],
        on_all_complete: Callable[[], None],
        stop_on_error: bool = True
    ) -> None:
        self._cancel_requested = False

        self._current_thread = threading.Thread(
            target=self._execute_worker,
            args=(statements, on_statement_complete, on_all_complete, stop_on_error),
            daemon=True
        )
        self._current_thread.start()

    def _execute_worker(
        self,
        statements: list[ParsedStatement],
        on_statement_complete: Callable[[ExecutionResult], None],
        on_all_complete: Callable[[], None],
        stop_on_error: bool
    ) -> None:
        try:
            for stmt in statements:
                if self._cancel_requested:
                    break

                result = self._execute_single(stmt)
                # Thread-safe UI update
                wx.CallAfter(on_statement_complete, result)

                if not result.success and stop_on_error:
                    break

        except Exception as ex:
            logger.error(f"Execution worker error: {ex}", exc_info=True)
        finally:
            wx.CallAfter(on_all_complete)

    def _execute_single(self, statement: ParsedStatement) -> ExecutionResult:
        start_time = time.time()

        try:
            self.session.context.execute(statement.text)

            elapsed_ms = (time.time() - start_time) * 1000

            cursor = self.session.context.cursor
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = self.session.context.fetchall()

                return ExecutionResult(
                    statement=statement,
                    success=True,
                    columns=columns,
                    rows=rows,
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

            return ExecutionResult(
                statement=statement,
                success=False,
                error=str(ex),
                elapsed_ms=elapsed_ms
            )

    def cancel(self) -> None:
        self._cancel_requested = True

    def is_running(self) -> bool:
        return self._current_thread is not None and self._current_thread.is_alive()


class QueryResultsRenderer:
    def __init__(self, notebook: wx.Notebook, session: Session):
        self.notebook = notebook
        self.session = session
        self._tab_counter = 0

    def create_result_tab(self, result: ExecutionResult) -> wx.Panel:
        self._tab_counter += 1

        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)

        if result.success and result.columns:
            grid = QueryEditorResultsDataViewCtrl(panel)
            self._populate_grid(grid, result)
            sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)

            tab_name = self._generate_tab_name(result)
        elif result.success:
            msg = wx.StaticText(panel, label=_("{} rows affected").format(result.affected_rows or 0))
            msg.SetFont(msg.GetFont().MakeBold())
            sizer.Add(msg, 1, wx.ALIGN_CENTER | wx.ALL, 20)

            tab_name = _("Query {}").format(self._tab_counter)
        else:
            error_panel = self._create_error_panel(panel, result)
            sizer.Add(error_panel, 1, wx.EXPAND | wx.ALL, 5)

            tab_name = _("Query {} (Error)").format(self._tab_counter)

        footer = self._create_footer(panel, result)
        sizer.Add(footer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        self.notebook.AddPage(panel, tab_name, select=True)

        return panel

    def _generate_tab_name(self, result: ExecutionResult) -> str:
        if result.columns and result.rows is not None:
            return _("Query {} ({} rows × {} cols)").format(
                self._tab_counter,
                len(result.rows),
                len(result.columns)
            )
        return _("Query {}").format(self._tab_counter)

    def _populate_grid(
        self,
        grid: QueryEditorResultsDataViewCtrl,
        result: ExecutionResult
    ) -> None:
        if not result.columns or not result.rows:
            return

        for col_name in result.columns:
            grid.AppendTextColumn(col_name, wx.dataview.DATAVIEW_CELL_INERT)

        model = grid.GetModel()
        if hasattr(model, 'data'):
            model.data = list(result.rows)
            model.Reset(len(result.rows))

    def _create_footer(self, parent: wx.Panel, result: ExecutionResult) -> wx.StaticText:
        parts = []

        if result.affected_rows is not None:
            parts.append(_("{} rows").format(result.affected_rows))

        parts.append(_("{:.1f} ms").format(result.elapsed_ms))

        if result.warnings:
            parts.append(_("{} warnings").format(len(result.warnings)))

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
        self._tab_counter = 0


class QueryEditorController:
    def __init__(
        self,
        stc_editor: wx.stc.StyledTextCtrl,
        results_notebook: wx.Notebook,
        session_provider: Callable[[], Optional[Session]]
    ):
        self.editor = stc_editor
        self.notebook = results_notebook
        self.get_session = session_provider

        self.parser: Optional[SQLStatementParser] = None
        self.selector = StatementSelector(stc_editor)
        self.executor: Optional[QueryExecutor] = None
        self.renderer: Optional[QueryResultsRenderer] = None

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

        self.executor.execute_statements(
            statements=statements_to_execute,
            on_statement_complete=self._on_statement_complete,
            on_all_complete=self._on_all_complete,
            stop_on_error=True
        )

    def _on_statement_complete(self, result: ExecutionResult) -> None:
        if self.renderer:
            self.renderer.create_result_tab(result)

    def _on_all_complete(self) -> None:
        logger.info("Query execution completed")


class QueryResultsController(QueryEditorController):
    def __init__(self, stc_sql_query: wx.stc.StyledTextCtrl, notebook_sql_results: wx.Notebook):
        from windows.main import CURRENT_SESSION

        super().__init__(
            stc_editor=stc_sql_query,
            results_notebook=notebook_sql_results,
            session_provider=lambda: CURRENT_SESSION.get_value()
        )
