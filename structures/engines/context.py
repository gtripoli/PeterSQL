import abc
import contextlib
import re

from typing import Dict, Any, Optional, List, Union, TypeAlias

from helpers.logger import logger
from helpers.observables import ObservableList, ObservableLazyList

from structures.ssh_tunnel import SSHTunnel

from structures.engines.datatype import StandardDataType
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger
from structures.engines.indextype import SQLIndexType, StandardIndexType

QUERY_LOGS: ObservableList[str] = ObservableList()

SQLTypeAlias: TypeAlias = Union['SQLView', 'SQLTrigger', 'SQLTable', 'SQLColumn', 'SQLIndex', 'SQLForeignKey', 'SQLRecord']


class AbstractColumnBuilder(abc.ABC):
    TEMPLATE: str

    parts: Dict[str, str]

    def __init__(self, column: 'SQLColumn', exclude: Optional[List[str]] = None):
        self.column = column
        self.exclude = exclude

        self.parts = {
            'name': self.name,
            'datatype': self.datatype,
            'unique': self.unique,
            'auto_increment': self.auto_increment,
            'nullable': self.nullable,
            'default': self.default,
            'collate': self.collate
        }

    @property
    def name(self):
        return f"`{self.column.name}`"

    @property
    def datatype(self):
        datatype_str = str(self.column.datatype.name)

        if self.column.datatype.has_length:
            datatype_str += f"({self.column.length or self.column.datatype.default_length})"

        if self.column.datatype.has_precision:
            if self.column.datatype.has_scale:
                datatype_str += f"({self.column.numeric_precision or self.column.datatype.default_precision},{self.column.numeric_scale or self.column.datatype.default_scale})"
            else:
                datatype_str += f"({self.column.numeric_precision or self.column.datatype.default_precision})"

        if self.column.datatype.has_set:
            datatype_str += f"({self.column.set or self.column.datatype.default_set})"

        return datatype_str

    @property
    def auto_increment(self):
        raise Exception("the auto increment should be defined in the engine column's table builder")

    @property
    def nullable(self):
        return 'NOT NULL' if not self.column.is_nullable or self.column.is_auto_increment else 'NULL'

    @property
    def default(self):
        return f"DEFAULT {self.column.server_default}" if self.column.server_default and self.column.server_default != '' else ''

    @property
    def collate(self):
        return f"CHARSET SET {self.column.table.database.context.COLLATION[self.column.collation_name]} COLLATE {self.column.collation_name}" if self.column.collation_name else ''

    @property
    def virtual(self):
        return f"GENERATED ALWAYS AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality and self.column.expression else ''

    @property
    def unique(self):
        return 'UNIQUE' if self.column.is_unique_key else ''

    # @property
    # def references(self):
    #     return f"REFERENCES {self.column.references}" if self.column.references else ''

    # @property
    # def constraint(self):
    #     return f"CONSTRAINT {self.column.constraint}" if self.column.constraint else ''

    def __str__(self) -> str:
        formatted_parts = []
        for template_part in self.TEMPLATE:
            if self.exclude and any(part in template_part for part in self.exclude):
                continue
            try:
                formatted = template_part % self.parts
            except Exception as ex:
                logger.error(ex, exc_info=True)

            if formatted_strip := formatted.strip():  # Only include non-empty parts
                formatted_parts.append(formatted_strip)

        return " ".join(formatted_parts)


class AbstractContext(abc.ABC):
    _connection: Any = None
    _cursor: Any = None
    _ssh_tunnel: Optional[SSHTunnel] = None

    ENGINES: List[str]
    DATATYPE: StandardDataType
    INDEXTYPE: StandardIndexType
    COLLATIONS: List[str]

    databases: ObservableLazyList[SQLDatabase]

    def __init__(self, session):
        self.session = session

        self.databases = ObservableLazyList(self.get_databases)

    @abc.abstractmethod
    def connect(self, **connect_kwargs) -> None:
        """Establish connection to the database using native driver"""
        raise NotImplementedError

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

    @property
    def connection(self) -> Any:
        if self._connection is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._connection

    @property
    def cursor(self) -> Any:
        if self._cursor is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._cursor

    def _on_connect(self, *args, **kwargs):
        logger.debug("connected")

    def _on_disconnect(self, *args, **kwargs):
        logger.debug("disconnected")

    def __del__(self):
        self.disconnect()

    @staticmethod
    def get_temporary_id(container: List[SQLTypeAlias]) -> int:
        return min([0] + [t.id for t in container]) - 1

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> Optional[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_databases(self) -> List[SQLDatabase]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_views(self, database: SQLDatabase) -> List[SQLView]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_triggers(self, database: SQLDatabase) -> List[SQLTrigger]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_indexes(self, table: SQLTable) -> List[SQLIndex]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_foreign_keys(self, table: SQLTable) -> List[SQLForeignKey]:
        raise NotImplementedError

    def get_records(self, table: SQLTable, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None) -> List[Dict[str, Any]]:
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

        query = [f"SELECT *",
                 f"FROM `{table.database.name}`.`{table.name}`",
                 f"{where}",
                 f"{order}",
                 f"LIMIT {limit} OFFSET {offset}",
                 ]

        self.execute(" ".join(query))

        return self.fetchall()

    @abc.abstractmethod
    def build_empty_table(self, database: SQLDatabase) -> SQLTable:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_column(self, table: SQLTable, datatype, **default_values) -> SQLColumn:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_index(self, name: str, type: SQLIndexType, table: SQLTable, columns: List[str]) -> SQLIndex:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_record(self, table: SQLTable, values: Dict[str, Any]) -> SQLRecord:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_foreign_key(self, name: str, table: SQLTable, columns: List[str]) -> SQLRecord:
        raise NotImplementedError

    # EXECUTION
    def execute(self, query: str) -> bool:
        query = re.sub(r'\s+', ' ', str(query)).strip()

        QUERY_LOGS.append(query)

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

    def fetchall(self) -> List[Any]:
        try:
            return self.cursor.fetchall()
        except Exception as ex:
            logger.error(ex, exc_info=True)
            raise

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
