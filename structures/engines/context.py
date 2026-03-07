import abc
import contextlib
import re

from typing import Any, Optional

import yaml

from constants import WORKDIR
from helpers.logger import logger
from helpers.observables import ObservableList, ObservableLazyList

from structures.helpers import SQLTypeAlias
from structures.ssh_tunnel import SSHTunnel
from structures.connection import Connection
from structures.engines.datatype import StandardDataType, SQLDataType
from structures.engines.database import (
    SQLDatabase,
    SQLTable,
    SQLColumn,
    SQLIndex,
    SQLCheck,
    SQLForeignKey,
    SQLRecord,
    SQLView,
    SQLTrigger,
)
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

    IDENTIFIER_QUOTE_CHAR: str = '"'
    DEFAULT_STATEMENT_SEPARATOR: str = ";"

    databases: ObservableLazyList[SQLDatabase]

    def __init__(self, connection: Connection):
        self.connection = connection

        self.databases = ObservableLazyList(self.get_databases)

    def __del__(self):
        self.disconnect()

    def before_connect(self, *args, **kwargs):
        # SSH tunnel support via connection configuration
        if hasattr(self.connection, "ssh_tunnel") and self.connection.ssh_tunnel:
            ssh_config = self.connection.ssh_tunnel
            if not ssh_config.is_enabled:
                return

            base_host = getattr(self, "_base_host", getattr(self, "host", "127.0.0.1"))
            base_port = getattr(self, "_base_port", getattr(self, "port", 0))
            self._base_host = base_host
            self._base_port = base_port

            remote_host = getattr(ssh_config, "remote_host", None) or getattr(
                self, "_base_host", "127.0.0.1"
            )
            remote_port = int(
                getattr(ssh_config, "remote_port", 0) or getattr(self, "_base_port", 0)
            )
            local_port = int(getattr(ssh_config, "local_port", 0) or 0)
            logger.debug(
                "Preparing DB SSH tunnel: connection=%s engine=%s base=%s:%s remote=%s:%s requested_local_port=%s",
                getattr(self.connection, "name", None),
                getattr(self.connection, "engine", None),
                self._base_host,
                self._base_port,
                remote_host,
                remote_port,
                local_port,
            )
            self._ssh_tunnel = SSHTunnel(
                ssh_config.hostname,
                int(ssh_config.port),
                ssh_username=ssh_config.username,
                ssh_password=ssh_config.password,
                remote_host=remote_host,
                remote_port=remote_port,
                local_bind_address=("127.0.0.1", local_port),
                ssh_executable=getattr(ssh_config, "executable", "ssh"),
                identity_file=getattr(ssh_config, "identity_file", None),
                extra_args=ssh_config.extra_args,
            )
            self._ssh_tunnel.start()

            self.host = "127.0.0.1"
            self.port = int(self._ssh_tunnel.local_port)
            logger.debug(
                "DB connection will use tunnel endpoint: %s:%s",
                self.host,
                self.port,
            )

    def after_connect(self, *args, **kwargs):
        pass

    def before_disconnect(self, *args, **kwargs):
        if self._ssh_tunnel is not None:
            logger.debug(
                "Stopping DB SSH tunnel for connection=%s",
                getattr(self.connection, "name", None),
            )
            self._ssh_tunnel.stop()
            self._ssh_tunnel = None

        if hasattr(self, "_base_host"):
            self.host = self._base_host

        if hasattr(self, "_base_port"):
            self.port = self._base_port

    def after_disconnect(self):
        pass

    @staticmethod
    def _extract_spec_names(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []

        names: list[str] = []
        for value in values:
            if isinstance(value, str):
                names.append(value)
                continue

            if isinstance(value, dict):
                if name := value.get("name"):
                    names.append(str(name))

        return names

    @staticmethod
    def _load_yaml_file(path: str) -> dict[str, Any]:
        file_path = WORKDIR / path
        if not file_path.exists():
            return {}

        with open(file_path, encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle)

        if not isinstance(data, dict):
            return {}

        return data

    @staticmethod
    def _merge_spec_values(
        base_values: list[str], add_values: list[str], remove_values: list[str]
    ) -> list[str]:
        removed = {value.upper() for value in remove_values}
        merged = [value for value in base_values if value.upper() not in removed]

        existing = {value.upper() for value in merged}
        for value in add_values:
            if value.upper() in existing:
                continue
            merged.append(value)
            existing.add(value.upper())

        return merged

    @staticmethod
    def _extract_major(version: Optional[str]) -> str:
        if not version:
            return ""

        if match := re.search(r"(\d+)", version):
            return match.group(1)

        return ""

    @staticmethod
    def _select_version_spec(
        versions_map: dict[str, Any], major_version: str
    ) -> dict[str, Any]:
        if not versions_map:
            return {}

        if major_version in versions_map and isinstance(
            versions_map[major_version], dict
        ):
            return versions_map[major_version]

        if not major_version.isdigit():
            return {}

        target_major = int(major_version)
        available_majors = [
            int(version)
            for version, value in versions_map.items()
            if version.isdigit() and isinstance(value, dict)
        ]
        if not available_majors:
            return {}

        eligible_majors = [major for major in available_majors if major <= target_major]
        if not eligible_majors:
            return {}

        selected_major = str(max(eligible_majors))
        selected_spec = versions_map.get(selected_major, {})
        if not isinstance(selected_spec, dict):
            return {}

        return selected_spec

    def get_engine_vocabulary(
        self, engine: str, server_version: Optional[str]
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        global_spec = self._load_yaml_file("structures/engines/specification.yaml")
        engine_spec = self._load_yaml_file(
            f"structures/engines/{engine}/specification.yaml"
        )

        global_common = (
            global_spec.get("common", {})
            if isinstance(global_spec.get("common", {}), dict)
            else {}
        )
        engine_common = (
            engine_spec.get("common", {})
            if isinstance(engine_spec.get("common", {}), dict)
            else {}
        )

        keywords = self._extract_spec_names(global_common.get("keywords", []))
        functions = self._extract_spec_names(global_common.get("functions", []))

        keywords = self._merge_spec_values(
            keywords,
            self._extract_spec_names(engine_common.get("keywords", [])),
            [],
        )
        functions = self._merge_spec_values(
            functions,
            self._extract_spec_names(engine_common.get("functions", [])),
            [],
        )

        major_version = self._extract_major(server_version)
        versions_map = (
            engine_spec.get("versions", {})
            if isinstance(engine_spec.get("versions", {}), dict)
            else {}
        )
        version_spec = self._select_version_spec(versions_map, major_version)

        keywords = self._merge_spec_values(
            keywords,
            [],
            self._extract_spec_names(version_spec.get("keywords_remove", [])),
        )
        functions = self._merge_spec_values(
            functions,
            [],
            self._extract_spec_names(version_spec.get("functions_remove", [])),
        )

        return tuple(sorted({value.upper() for value in keywords})), tuple(
            sorted({value.upper() for value in functions})
        )

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
    def set_database(self, database: SQLDatabase) -> None:
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
    def build_empty_table(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> SQLTable:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_column(
        self,
        table: SQLTable,
        datatype: SQLDataType,
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> SQLColumn:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_index(
        self,
        table: SQLTable,
        indextype: SQLIndexType,
        columns: list[str],
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> SQLIndex:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_check(
        self,
        table: SQLTable,
        /,
        name: Optional[str] = None,
        expression: Optional[str] = None,
        **default_values,
    ) -> SQLCheck:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_foreign_key(
        self,
        table: SQLTable,
        columns: list[str],
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> SQLForeignKey:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_record(
        self, table: SQLTable, /, *, values: dict[str, Any]
    ) -> SQLRecord:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_view(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> SQLView:
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_function(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> "SQLFunction":
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_procedure(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> "SQLProcedure":
        raise NotImplementedError

    @abc.abstractmethod
    def build_empty_trigger(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> SQLTrigger:
        raise NotImplementedError

    def quote_identifier(self, name: str) -> str:
        value = name.strip()
        if not value:
            assert False, "Invalid identifier name: %s" % name

        if SQL_SAFE_NAME_REGEX.match(value):
            return value

        escaped_name = value.replace(
            self.IDENTIFIER_QUOTE_CHAR, self.IDENTIFIER_QUOTE_CHAR * 2
        )
        return f"{self.IDENTIFIER_QUOTE_CHAR}{escaped_name}{self.IDENTIFIER_QUOTE_CHAR}"

    def qualify(self, *parts):
        return ".".join(self.quote_identifier(part) for part in parts)

    def get_records(
        self,
        table: SQLTable,
        /,
        *,
        filters: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
        orders: Optional[str] = None,
    ) -> list[dict[str, Any]]:
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

        database_identifier = table.database.quoted_name if table.database else ""
        table_identifier = table.quoted_name

        if database_identifier:
            from_clause = f"{database_identifier}.{table_identifier}"
        else:
            from_clause = table_identifier

        query = [
            f"SELECT *",
            f"FROM {from_clause}",
            f"{where}",
            f"{order}",
            f"LIMIT {limit} OFFSET {offset}",
        ]

        self.execute(" ".join(query))

        return self.fetchall()

    # EXECUTION
    def execute(self, query: str) -> bool:
        query_clean = re.sub(r"\s+", " ", str(query)).strip()
        logger.debug("execute query: %s", query_clean)
        QUERY_LOGS.append(query_clean)

        try:
            self.cursor.execute(query)
        except Exception as ex:
            logger.error(query)
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
        self.before_disconnect()

        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None

        if self._connection is not None:
            self._connection.close()
            self._connection = None

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
