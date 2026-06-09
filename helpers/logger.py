import faulthandler
import logging
import sys
import threading

from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Optional, TextIO

LOG_FMT = "%(asctime)s %(process)s %(levelname)s %(name)s: %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"

_fault_log_stream: Optional[TextIO] = None


def _log_unhandled_exception(
        source: str,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: Optional[TracebackType],
) -> None:
    logger.critical(
        f"Unhandled exception from {source}",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def configure_logging(log_file_path: Path) -> None:
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATE_FMT)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not any(isinstance(handler, logging.StreamHandler) for handler in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    if not any(
            isinstance(handler, RotatingFileHandler)
            and Path(handler.baseFilename) == log_file_path
            for handler in root_logger.handlers
    ):
        file_handler = RotatingFileHandler(
            filename=log_file_path,
            mode="a",
            maxBytes=10_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def enable_fault_handler(fault_log_path: Path) -> None:
    global _fault_log_stream

    fault_log_path.parent.mkdir(parents=True, exist_ok=True)
    _fault_log_stream = fault_log_path.open(mode="a", encoding="utf-8")
    faulthandler.enable(file=_fault_log_stream, all_threads=True)


def install_global_exception_hooks() -> None:
    def _main_excepthook(
            exc_type: type[BaseException],
            exc_value: BaseException,
            exc_traceback: Optional[TracebackType],
    ) -> None:
        _log_unhandled_exception("sys.excepthook", exc_type, exc_value, exc_traceback)

    def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
        _log_unhandled_exception(
            f"threading.excepthook thread={args.thread.name}",
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
        )

    def _unraisablehook(args: sys.UnraisableHookArgs) -> None:
        exc_value = args.exc_value
        if exc_value is None:
            exc_value = RuntimeError("unraisable exception without exc_value")

        _log_unhandled_exception(
            "sys.unraisablehook",
            type(exc_value),
            exc_value,
            args.exc_traceback,
        )

    sys.excepthook = _main_excepthook
    threading.excepthook = _thread_excepthook
    sys.unraisablehook = _unraisablehook

logger = logging.getLogger("PeterSQL")
logger.setLevel(logging.DEBUG)
