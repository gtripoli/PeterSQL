import contextlib
import dataclasses
import threading
import time

from typing import Any, Callable, Optional

import wx

from helpers.loader import Loader
from helpers.logger import logger

from structures.session import Session
from structures.connection import Connection, ConnectionEngine
from structures.engines.datatype import SQLDataType

from windows.main.query.parser import ParsedStatement


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
    connection_lost: bool = False


@dataclasses.dataclass
class ExecutionSummary:
    total_statements: int = 0
    completed_statements: int = 0
    successful_statements: int = 0
    failed_statements: int = 0
    elapsed_ms: float = 0.0
    cancelled: bool = False
    last_statement: Optional[ParsedStatement] = None


class QueryExecutor:
    def __init__(self, session: Session):
        self.session = session
        self._cancel_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._worker_context: Optional[Any] = None
        self._loader_context: Optional[Any] = None
        self._lock = threading.Lock()

    def execute_statements(
            self,
            statements: list[ParsedStatement],
            on_statement_complete: Callable[[ExecutionResult], None],
            on_all_complete: Callable[[ExecutionSummary], None],
            current_database: Optional[Any] = None,
            stop_on_error: bool = True
    ) -> None:
        if self._current_thread and self._current_thread.is_alive():
            logger.warning("Attempted to start a new execution while one is already running.")
            return

        self._cancel_requested = False
        self._loader_context = Loader.cursor_wait()
        self._loader_context.__enter__()

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

    def _dispatch_statement_result(
            self,
            on_statement_complete: Callable[[ExecutionResult], None],
            result: ExecutionResult,
    ) -> None:
        ui_done_event = threading.Event()

        def _on_ui_thread() -> None:
            try:
                on_statement_complete(result)
            finally:
                ui_done_event.set()

        wx.CallAfter(_on_ui_thread)
        while not ui_done_event.wait(0.05):
            continue

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

            wx.CallAfter(self._stop_loader)
            wx.CallAfter(on_all_complete, summary)

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

            from structures.engines.context import ConnectionLostError
            connection_lost = isinstance(ex, ConnectionLostError)

            return ExecutionResult(
                statement=statement,
                success=False,
                error=str(ex),
                cancelled=is_cancelled,
                elapsed_ms=elapsed_ms,
                connection_lost=connection_lost,
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

        if self.session.engine == ConnectionEngine.POSTGRESQL:
            connect_kwargs = {
                "skip_before_connect": True,
                "skip_after_connect": True,
            }

            if current_database is not None and hasattr(current_database, "name"):
                connect_kwargs["database"] = current_database.name

            context.connect(**connect_kwargs)
            return context

        context.connect(skip_before_connect=True, skip_after_connect=True, database=current_database.name if current_database is not None else None)

        # if current_database is not None:
        #     with contextlib.suppress(Exception):
        #         context.set_database(current_database)

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

    def _stop_loader(self) -> None:
        if self._loader_context is not None:
            self._loader_context.__exit__(None, None, None)
            self._loader_context = None

    def cancel(self) -> None:
        self._cancel_requested = True
        self._clear_worker_context()

    def is_running(self) -> bool:
        return self._current_thread is not None and self._current_thread.is_alive()