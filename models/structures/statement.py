import re
import abc
import uuid

from typing import Dict, Any, Optional, List, NamedTuple

from helpers.logger import logger
from helpers.observables import ObservableArray

from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey

LOG_QUERY: ObservableArray[str] = ObservableArray()


class ParsedColumnType(NamedTuple):
    name: str
    precision: Optional[int] = None
    scale: Optional[int] = None
    length: Optional[int] = None
    set: Optional[List[str]] = None
    is_unsigned: Optional[bool] = False
    is_zerofill: Optional[bool] = False


class AbstractStatement(abc.ABC):
    _connection: Any = None
    _cursor: Any = None

    def __init__(self, connection_url):
        self.connection_url = connection_url

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

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _on_connect(self, *args, **kwargs):
        logger.debug("connected")

    def _on_disconnect(self, *args, **kwargs):
        logger.debug("disconnected")

    @staticmethod
    def parse_type(column_definition: str) -> ParsedColumnType:
        match = re.search(r'(\w+)\s*\((\d+)(?:,\s*(\d+))?\)(\s*unsigned)?(\s*zerofill)?', column_definition)
        if match:
            return ParsedColumnType(
                name=match.group(1).upper(),
                precision=int(match.group(2)),
                scale=int(match.group(3)) if match.group(3) else None,
                is_unsigned=bool(match.group(4)),
                is_zerofill=bool(match.group(5))
            )

        match = re.search(r'^(enum|set)\((.*)\)$', column_definition)
        if match:
            return ParsedColumnType(
                name=match.group(1).upper(),
                set=[value.strip("'") for value in match.group(2).split(",")]
            )

        return ParsedColumnType(name=column_definition.upper())

    @staticmethod
    def generate_uuid(length: int = 8) -> str:
        return str(uuid.uuid4())[::-1][:length]

    @staticmethod
    def build_column_definition(table: SQLTable, column: SQLColumn) -> str:
        d = column.get_definition()
        parts = [d['name'], d['datatype'], d['nullable']]
        if 'default' in d:
            parts.append(d['default'])
        if 'collation' in d:
            parts.append(d['collation'])
        if 'comment' in d:
            parts.append(d['comment'])
        if 'virtual' in d:
            parts.append(d['virtual'])
        return ' '.join(parts)

    # General abstract methods
    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> Optional[int]:
        raise NotImplementedError

    # Database abstract methods
    @abc.abstractmethod
    def get_databases(self) -> List[SQLDatabase]:
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

    @abc.abstractmethod
    def get_records(self, database: SQLDatabase, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[Dict]:
        raise NotImplementedError

    # Table abstract methods
    @abc.abstractmethod
    def build_empty_table(self, database: SQLDatabase) -> SQLTable:
        raise NotImplementedError

    @abc.abstractmethod
    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def alter_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    # General column methods
    def _add_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` ADD COLUMN {self.build_column_definition(table, column)}"
        if hasattr(column, 'after') and column.after:
            sql += f" AFTER `{column.after}`"
        self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` MODIFY COLUMN {self.build_column_definition(table, column)}"
        self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` DROP COLUMN `{column.name}`"
        self.execute(sql)

    # Execution
    def execute(self, query: str, params=None, **kwargs) -> bool:
        query = re.sub(r'\s+', ' ', str(query)).strip()

        LOG_QUERY.append(query)

        try:
            if params is not None:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query, **kwargs)

        except Exception as ex:
            logger.error(ex, exc_info=True)
            LOG_QUERY.append(f"/* {str(ex)} */")
            raise

        return True

    def __call__(self, database: SQLDatabase, table: SQLTable) -> Optional[bool]:
        if not table :
            return

        if table.id == -1:
            method = self.create_table
        else:
            method = self.alter_table

        result = method(database, table)
        database.tables.clear()

        return result



class Transaction:
    def __init__(self, statement: AbstractStatement):
        self.statement = statement

    def __enter__(self):
        self.statement.execute("BEGIN")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.statement.execute("COMMIT")
            logger.info("Transaction committed")
        else:
            self.statement.execute("ROLLBACK")
            logger.error(f"Transaction failed: {exc_val}")
