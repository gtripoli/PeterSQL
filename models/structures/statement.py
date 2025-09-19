import re
import abc

from typing import Dict, Iterator, Any

from helpers.logger import logger

from helpers.observables import ObservableArray
from models.structures.database import SQLDatabase, SQLTable, SQLColumn

LOG_QUERY: ObservableArray[str] = ObservableArray()


class AbstractStatement(abc.ABC):
    _connection = None
    _cursor = None

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
        print("CONNECTED", args, kwargs)

    def _on_disconnect(self, *args, **kwargs):
        print("DISCONNECTED", args, kwargs)

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_databases(self) -> Iterator[SQLDatabase]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tables(self, database: str) -> Iterator[SQLTable]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_columns(self, database: str, table: str) -> Iterator[SQLColumn]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> Iterator[Dict]:
        raise NotImplementedError

    def execute(self, query: str, **kwargs) -> Any:
        query = re.sub(r'\s+', ' ', str(query)).strip()

        LOG_QUERY.append(query)

        try:
            self.cursor.execute(query, kwargs)
            return self.cursor
        except Exception as ex:
            logger.error(ex, exc_info=True)
            LOG_QUERY.append(str(ex))
            raise

    @abc.abstractmethod
    def update_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError