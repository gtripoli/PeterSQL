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
from structures.engines.database import SQLTable, SQLRecord

from windows.main.query.executor import QueryExecutor
from windows.state import CURRENT_DATABASE


@dataclasses.dataclass
class RecordsOperationResult:
    operation: str
    success: bool
    records: Optional[list[SQLRecord]] = None
    affected_records: Optional[int] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    cancelled: bool = False
    warnings: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class RecordsOperationSummary:
    total_operations: int = 0
    completed_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    elapsed_ms: float = 0.0
    cancelled: bool = False
    last_operation: Optional[str] = None


class RecordsExecutor:
    def __init__(self, session: Session):
        self.session = session
        self._cancel_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._worker_context: Optional[Any] = None
        self._loader_context: Optional[Any] = None
        self._lock = threading.Lock()

    def load_records(
            self,
            table: SQLTable,
            on_complete: Callable[[RecordsOperationResult], None],
            filters: Optional[str] = None,
            limit: int = 1000,
            offset: int = 0,
            orders: Optional[str] = None
    ) -> None:
        self._execute_operation(
            operation="load_records",
            on_complete=on_complete,
            table=table,
            filters=filters,
            limit=limit,
            offset=offset,
            orders=orders
        )

    def _execute_operation(self, **kwargs) -> None:
        self._cancel_requested = False
        self._loader_context = Loader.cursor_wait()
        self._loader_context.__enter__()

        self._current_thread = threading.Thread(
            target=self._execute_worker,
            args=(kwargs,),
            daemon=True
        )
        self._current_thread.start()

    def _dispatch_operation_result(
            self,
            on_complete: Callable[[RecordsOperationResult], None],
            result: RecordsOperationResult,
    ) -> None:
        ui_done_event = threading.Event()

        def _on_ui_thread() -> None:
            try:
                on_complete(result)
            finally:
                ui_done_event.set()

        wx.CallAfter(_on_ui_thread)
        while not ui_done_event.wait(0.05):
            continue

    def _execute_worker(self, operation_kwargs: dict) -> None:
        time_start = time.perf_counter()
        operation = operation_kwargs.get("operation", "unknown")
        on_complete = operation_kwargs.get("on_complete")

        try:
            context = self._create_worker_context()
            self._set_worker_context(context)

            result = self._execute_single_operation(context, operation_kwargs)

            self._dispatch_operation_result(on_complete, result)

        except Exception as ex:
            logger.error(f"Records executor error: {ex}", exc_info=True)
            error_result = RecordsOperationResult(
                operation=operation,
                success=False,
                error=str(ex),
                elapsed_ms=(time.perf_counter() - time_start) * 1000
            )
            self._dispatch_operation_result(on_complete, error_result)
        finally:
            self._clear_worker_context()
            wx.CallAfter(self._stop_loader)

    def _execute_single_operation(self, context: Any, operation_kwargs: dict) -> RecordsOperationResult:
        start_time = time.time()
        operation = operation_kwargs.get("operation", "unknown")

        try:
            if operation == "load_records":
                return self._load_records_operation(context, operation_kwargs)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as ex:
            elapsed_ms = (time.time() - start_time) * 1000
            is_cancelled = self._cancel_requested

            return RecordsOperationResult(
                operation=operation,
                success=False,
                error=str(ex),
                cancelled=is_cancelled,
                elapsed_ms=elapsed_ms
            )

    def _load_records_operation(self, context: Any, operation_kwargs: dict) -> RecordsOperationResult:
        start_time = time.time()
        table = operation_kwargs.get("table")
        filters = operation_kwargs.get("filters")
        limit = operation_kwargs.get("limit", 1000)
        offset = operation_kwargs.get("offset", 0)
        orders = operation_kwargs.get("orders")

        records = context.get_records(
            table,
            filters=filters,
            limit=limit,
            offset=offset,
            orders=orders
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return RecordsOperationResult(
            operation="load_records",
            success=True,
            records=records,
            affected_records=len(records),
            elapsed_ms=elapsed_ms
        )


    def _build_worker_connection(self) -> Connection:
        """Build a worker connection similar to QueryExecutor."""
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

    def _create_worker_context(self) -> Any:
        """Create a worker context similar to QueryExecutor."""
        context = self.session._get_context_class()(self._build_worker_connection())

        # if self.session.engine == ConnectionEngine.POSTGRESQL:
        #     connect_kwargs = {
        #         "skip_before_connect": True,
        #         "skip_after_connect": True,
        #     }
        #     context.connect(**connect_kwargs)
        #     return context

        context.connect(skip_before_connect=True, skip_after_connect=True, database=CURRENT_DATABASE.get_value().name)
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
