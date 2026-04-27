from typing import Any, Callable, Optional
from gettext import gettext as _

import wx
import wx.stc

from helpers.logger import logger

from structures.session import Session

from windows.main.query.parser import ExecutionMode, SQLStatementParser, StatementSelector
from windows.main.query.executor import ExecutionResult, ExecutionSummary, QueryExecutor
from windows.main.query.renderer import QueryResultsRenderer


class QueryEditorController:
    def __init__(
            self,
            stc_editor: wx.stc.StyledTextCtrl,
            results_notebook: wx.Notebook,
            session_provider: Callable[[], Optional[Session]],
            database_provider: Optional[Callable[[], Optional[Any]]] = None,
            cancel_button: Optional[wx.Button] = None,
            on_new_query: Optional[Callable[[wx.Event], None]] = None,
            on_close_query: Optional[Callable[[wx.Event], None]] = None,
            on_save_query: Optional[Callable[[wx.Event], None]] = None,
            on_save_as_query: Optional[Callable[[wx.Event], None]] = None,
            on_stop_state_changed: Optional[Callable[[bool], None]] = None,
            on_before_execute: Optional[Callable[[], bool]] = None,
    ):
        self.editor = stc_editor
        self.notebook = results_notebook
        self.get_session = session_provider
        self.get_database = database_provider or (lambda: None)
        self.cancel_button = cancel_button
        self.on_new_query = on_new_query
        self.on_close_query = on_close_query
        self.on_save_query = on_save_query
        self.on_save_as_query = on_save_as_query
        self.on_stop_state_changed = on_stop_state_changed
        self.on_before_execute = on_before_execute

        self.parser: Optional[SQLStatementParser] = None
        self.selector = StatementSelector(stc_editor)
        self.executor: Optional[QueryExecutor] = None
        self.renderer: Optional[QueryResultsRenderer] = None
        self._cancel_feedback_pending = False
        self._shortcuts = self._load_shortcuts()

        self._bind_shortcuts()
        self._set_cancel_button_enabled(False)

    def _load_shortcuts(self) -> dict[str, str]:
        settings = wx.GetApp().settings
        return {
            "execute_current": settings.get_value("ui", "shortcuts", "query", "execute_current", default="Ctrl+Enter"),
            "execute_all": settings.get_value("ui", "shortcuts", "query", "execute_all", default="Ctrl+Shift+Enter"),
            "stop": settings.get_value("ui", "shortcuts", "query", "stop", default="Esc"),
            "new_query": settings.get_value("ui", "shortcuts", "query", "new_query", default="Ctrl+T"),
            "close_query": settings.get_value("ui", "shortcuts", "query", "close_query", default="Ctrl+W"),
            "save": settings.get_value("ui", "shortcuts", "query", "save", default="Ctrl+S"),
            "save_as": settings.get_value("ui", "shortcuts", "query", "save_as", default="Ctrl+Shift+S"),
        }

    @staticmethod
    def _matches_shortcut_key(key_name: str, key_code: int) -> bool:
        if key_name == "enter":
            return key_code in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]

        if key_name == "esc":
            return key_code == wx.WXK_ESCAPE

        if len(key_name) == 1:
            return key_code == ord(key_name.upper())

        return False

    def _matches_shortcut(self, event: wx.KeyEvent, shortcut: str) -> bool:
        parts = [part.strip().lower() for part in shortcut.split("+") if part.strip()]
        if not parts:
            return False

        key_name = parts[-1]
        modifiers = set(parts[:-1])

        if event.ControlDown() != ("ctrl" in modifiers):
            return False

        if event.ShiftDown() != ("shift" in modifiers):
            return False

        if event.AltDown() != ("alt" in modifiers):
            return False

        key_code = event.GetKeyCode()
        return self._matches_shortcut_key(key_name, key_code)

    def _bind_shortcuts(self) -> None:
        self.editor.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _set_cancel_button_enabled(self, enabled: bool) -> None:
        if self.cancel_button is not None:
            self.cancel_button.Enable(enabled)

        if self.on_stop_state_changed is not None:
            self.on_stop_state_changed(enabled)

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

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        if self._matches_shortcut(event, self._shortcuts["execute_current"]):
            self.execute_current(event)
            return

        if self._matches_shortcut(event, self._shortcuts["execute_all"]):
            self.execute_all(event)
            return

        if self._matches_shortcut(event, self._shortcuts["stop"]):
            self.cancel_execution(event)
            return

        if self._matches_shortcut(event, self._shortcuts["new_query"]) and self.on_new_query is not None:
            self.on_new_query(event)
            return

        if self._matches_shortcut(event, self._shortcuts["close_query"]) and self.on_close_query is not None:
            self.on_close_query(event)
            return

        if self._matches_shortcut(event, self._shortcuts["save_as"]) and self.on_save_as_query is not None:
            self.on_save_as_query(event)
            return

        if self._matches_shortcut(event, self._shortcuts["save"]) and self.on_save_query is not None:
            self.on_save_query(event)
            return

        event.Skip()

    def _execute(self, mode: ExecutionMode) -> None:
        if self.on_before_execute is not None and not self.on_before_execute():
            return

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

    def _on_all_complete(self, summary: ExecutionSummary) -> None:
        self._set_cancel_button_enabled(False)

        if summary.cancelled and self._cancel_feedback_pending:
            self._show_cancel_message(summary)

        self._cancel_feedback_pending = False
        logger.info("Query execution completed")

    def get_shortcuts(self) -> dict[str, str]:
        return dict(self._shortcuts)

    def execute_all(self, event: wx.Event) -> None:
        self._execute(ExecutionMode.ALL)

    def execute_current(self, event: wx.Event) -> None:
        self._execute(ExecutionMode.CURRENT)

    def cancel_execution(self, event: wx.Event) -> None:
        if self.executor and self.executor.is_running():
            self._cancel_feedback_pending = True
            self.executor.cancel()
            logger.info("Query execution cancelled")


class QueryResultsController(QueryEditorController):
    def __init__(
            self,
            stc_sql_query: wx.stc.StyledTextCtrl,
            notebook_sql_results: wx.Notebook,
            cancel_button: Optional[wx.Button] = None,
            on_new_query: Optional[Callable[[wx.Event], None]] = None,
            on_close_query: Optional[Callable[[wx.Event], None]] = None,
            on_save_query: Optional[Callable[[wx.Event], None]] = None,
            on_save_as_query: Optional[Callable[[wx.Event], None]] = None,
            on_stop_state_changed: Optional[Callable[[bool], None]] = None,
            on_before_execute: Optional[Callable[[], bool]] = None,
    ):
        from windows.main import CURRENT_DATABASE, CURRENT_SESSION  # Lazy import: unavoidable circular dependency.

        super().__init__(
            stc_editor=stc_sql_query,
            results_notebook=notebook_sql_results,
            session_provider=lambda: CURRENT_SESSION.get_value(),
            database_provider=lambda: CURRENT_DATABASE.get_value(),
            cancel_button=cancel_button,
            on_new_query=on_new_query,
            on_close_query=on_close_query,
            on_save_query=on_save_query,
            on_save_as_query=on_save_as_query,
            on_stop_state_changed=on_stop_state_changed,
            on_before_execute=on_before_execute,
        )
