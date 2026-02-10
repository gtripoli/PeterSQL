import abc
import contextlib
import re

from typing import Any, Optional

from helpers.logger import logger
from helpers.observables import ObservableList, ObservableLazyList

from structures.helpers import SQLTypeAlias
from structures.ssh_tunnel import SSHTunnel
from structures.connection import Connection
from structures.engines.datatype import StandardDataType, SQLDataType
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger
from structures.engines.indextype import SQLIndexType, StandardIndexType

QUERY_LOGS: ObservableList[str] = ObservableList()

SQL_SAFE_NAME_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class AbstractContext(abc.ABC):
    _connection: Any = None
    _cursor: Any = None
    _ssh_tunnel: Optional[SSHTunnel] = None

    ENGINES: list[str] = []
    KEYWORDS: tuple[str, ...] = ()
    FUNCTIONS: tuple[str, ...] = ()
    DATATYPE: StandardDataType
    INDEXTYPE: StandardIndexType
    COLLATIONS: dict[str, str] = {}

    IDENTIFIER_QUOTE: str = '"'

    databases: ObservableLazyList[SQLDatabase]

    def __init__(self, connection: Connection):
        self.connection = connection

        self.databases = ObservableLazyList(self.get_databases)

    def __del__(self):
        self.disconnect()

    def _on_connect(self, *args, **kwargs):
        logger.debug("connected")

    def _on_disconnect(self, *args, **kwargs):
        logger.debug("disconnected")

    @property
    def is_connected(self):
        return self._connection is not None and self._cursor is not None

    @property
    def cursor(self) -> Any:
        if self._cursor is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._cursor

    @staticmethod
    def get_temporary_id(container: list[SQLTypeAlias]) -> int:
        return min([0] + [t.id for t in container]) - 1

    @abc.abstractmethod
    def connect(self, **connect_kwargs) -> None:
        """Establish connection to the database using native driver"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> Optional[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_databases(self) -> list[SQLDatabase]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_views(self, database: SQLDatabase) -> list[SQLView]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_triggers(self, database: SQLDatabase) -> list[SQLTrigger]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tables(self, database: SQLDatabase) -> list[SQLTable]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_columns(self, table: SQLTable) -> list[SQLColumn]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_indexes(self, table: SQLTable) -> list[SQLIndex]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_foreign_keys(self, table: SQLTable) -> list[SQLForeignKey]:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_table(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> SQLTable:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_column(self, table: SQLTable, datatype: SQLDataType, /, name: Optional[str] = None, **default_values) -> SQLColumn:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_index(self, table: SQLTable, indextype: SQLIndexType, columns: list[str], /, name: Optional[str] = None, **default_values) -> SQLIndex:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_foreign_key(self, table: SQLTable, columns: list[str], /, name: Optional[str] = None, **default_values) -> SQLForeignKey:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_record(self, table: SQLTable, /, *, values: dict[str, Any]) -> SQLRecord:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_view(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> SQLView:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_trigger(self, database: SQLDatabase, /, name: Optional[str] = None, **default_values) -> SQLTrigger:
        raise NotImplementedError

    def build_sql_safe_name(self, name: Optional[str]) -> str:
        value = (name or "").strip()
        if not value:
            return value

        if SQL_SAFE_NAME_REGEX.match(value):
            return value

        escaped_name = value.replace(self.IDENTIFIER_QUOTE, self.IDENTIFIER_QUOTE * 2)
        return f"{self.IDENTIFIER_QUOTE}{escaped_name}{self.IDENTIFIER_QUOTE}"

    def get_records(self, table: SQLTable, /, *, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None) -> list[dict[str, Any]]:
        logger.debug(f"get records for table={table.name}")
        QUERY_LOGS.append(f"/* get_records for table={table.name} */")
        if table is None or table.is_new:
            return []

        order = ""
        where = ""
        if filters:
            where = f"WHERE {filters}"

        if orders:
            order = f"ORDER BY {orders}"

        database_identifier = table.database.sql_safe_name if table.database else ""
        table_identifier = table.sql_safe_name

        if database_identifier:
            from_clause = f"{database_identifier}.{table_identifier}"
        else:
            from_clause = table_identifier

        query = [f"SELECT *",
                 f"FROM {from_clause}",
                 f"{where}",
                 f"{order}",
                 f"LIMIT {limit} OFFSET {offset}",
                 ]

        self.execute(" ".join(query))

        return self.fetchall()

    # EXECUTION
    def execute(self, query: str) -> bool:
        query_clean = re.sub(r'\s+', ' ', str(query)).strip()
        logger.debug("execute query: %s", query_clean)
        QUERY_LOGS.append(query_clean)

        try:
            self.cursor.execute(query)
        except Exception as ex:
            logger.error(query)
            logger.error(ex, exc_info=True)
            QUERY_LOGS.append(f"/* {str(ex)} */")
            raise

        return True

    def fetchone(self) -> Any:
        try:
            return self.cursor.fetchone()
        except Exception as ex:
            logger.error(ex, exc_info=True)
            raise

    def fetchall(self) -> list[Any]:
        try:
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(ex, exc_info=True)
            raise

    def disconnect(self) -> None:
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None

        if self._connection is not None:
            self._connection.close()
            self._connection = None

        if self._ssh_tunnel is not None:
            self._ssh_tunnel.stop()
            self._ssh_tunnel = None

    @contextlib.contextmanager
    def transaction(self):
        try:
            self.execute("BEGIN")
            yield self
            self.execute("COMMIT")
        except Exception as ex:
            self.execute("ROLLBACK")
            logger.error(ex, exc_info=True)
            QUERY_LOGS.append(f"/* {str(ex)} */")
            raise
