import re
import ssl
from typing import Any, Optional

import pymysql

from gettext import gettext as _

from helpers.logger import logger
from structures.connection import Connection

from structures.engines.context import QUERY_LOGS, AbstractContext
from structures.engines.database import (
    SQLColumn,
    SQLDatabase,
    SQLForeignKey,
    SQLIndex,
    SQLTable,
)
from structures.engines.datatype import SQLDataType

from structures.engines.mysql import MAP_COLUMN_FIELDS
from structures.engines.mysql.database import (
    MySQLColumn,
    MySQLDatabase,
    MySQLForeignKey,
    MySQLIndex,
    MySQLProcedure,
    MySQLRecord,
    MySQLTable,
    MySQLTrigger,
    MySQLView,
)
from structures.engines.mysql.datatype import MySQLDataType
from structures.engines.mysql.indextype import MySQLIndexType

from structures.ssh_tunnel import SSHTunnel


class MySQLContext(AbstractContext):
    MAP_COLUMN_FIELDS = MAP_COLUMN_FIELDS

    DATATYPE = MySQLDataType
    INDEXTYPE = MySQLIndexType

    IDENTIFIER_QUOTE_CHAR = "`"
    DEFAULT_STATEMENT_SEPARATOR = ";"

    def __init__(self, connection: Connection):
        super().__init__(connection)

        self.host = connection.configuration.hostname
        self.user = connection.configuration.username
        self.password = connection.configuration.password
        # self.database = session.configuration.database
        self.port = getattr(connection.configuration, "port", 3306)

    def after_connect(self, *args, **kwargs):
        super().after_connect(*args, **kwargs)
        self.execute("""
            SELECT COLLATION_NAME, CHARACTER_SET_NAME FROM information_schema.COLLATIONS
            WHERE CHARACTER_SET_NAME IS NOT NULL
            ORDER BY CHARACTER_SET_NAME, COLLATION_NAME;
        """)
        for row in self.fetchall():
            self.COLLATIONS[row["COLLATION_NAME"]] = row["CHARACTER_SET_NAME"]

        self.execute("""SHOW ENGINES;""")
        self.ENGINES = [dict(row).get("Engine") for row in self.fetchall()]

        server_version = self.get_server_version()
        self.KEYWORDS, builtin_functions = self.get_engine_vocabulary(
            "mysql", server_version
        )

        self.execute("""
            SELECT DISTINCT ROUTINE_NAME FROM information_schema.ROUTINES
            WHERE ROUTINE_TYPE = 'FUNCTION'
            ORDER BY ROUTINE_NAME;
        """)
        user_functions = tuple(row["ROUTINE_NAME"].upper() for row in self.fetchall())

        self.FUNCTIONS = tuple(dict.fromkeys(builtin_functions + user_functions))

    def _parse_type(self, column_type: str):
        types = MySQLDataType.get_all()
        type_set = [
            x.lower()
            for type in types
            if type.has_set
            for x in ([type.name] + type.alias)
        ]
        type_length = [
            x.lower()
            for type in types
            if type.has_length
            for x in ([type.name] + type.alias)
        ]

        if match := re.search(rf"^({'|'.join(type_set)})\((.*)\)$", column_type):
            return dict(
                name=match.group(1).upper(),
                set=[value.strip("'") for value in match.group(2).split(",")],
            )
        if match := re.search(rf"^({'|'.join(type_length)})\((.*)\)$", column_type):
            return dict(name=match.group(1).upper(), length=int(match.group(2)))

        if match := re.search(
            r"(\w+)\s*\((\d+)(?:,\s*(\d+))?\)(\s*unsigned)?(\s*zerofill)?", column_type
        ):
            return dict(
                name=match.group(1).upper(),
                precision=int(match.group(2)),
                scale=int(match.group(3)) if match.group(3) else None,
                is_unsigned=bool(match.group(4)),
                is_zerofill=bool(match.group(5)),
            )

        return dict()

    def connect(self, **connect_kwargs) -> None:
        if self._connection is None:
            self.before_connect()

            use_tls_enabled = bool(
                getattr(self.connection.configuration, "use_tls_enabled", False)
            )

            base_kwargs = dict(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor,
                **connect_kwargs,
            )
            if use_tls_enabled:
                base_kwargs["ssl"] = {
                    "cert_reqs": ssl.CERT_NONE,
                    "check_hostname": False,
                }
            logger.debug(
                "MySQL connect target host=%s port=%s user=%s use_tls_enabled=%s",
                base_kwargs.get("host"),
                base_kwargs.get("port"),
                base_kwargs.get("user"),
                use_tls_enabled,
            )

            try:
                self._connection = pymysql.connect(**base_kwargs)
                self._cursor = self._connection.cursor()
            except pymysql.err.OperationalError as e:
                should_retry_tls = bool(e.args and e.args[0] == 1045)
                if not should_retry_tls or "ssl" in base_kwargs:
                    logger.error(f"Failed to connect to MySQL: {e}")
                    raise

                logger.warning(
                    "MySQL connection failed without TLS (%s). Retrying with TLS.",
                    e,
                )
                logger.debug(
                    "Retrying MySQL connection with TLS preferred after auth failure"
                )
                tls_kwargs = {
                    **base_kwargs,
                    "ssl": {
                        "cert_reqs": ssl.CERT_NONE,
                        "check_hostname": False,
                    },
                }
                self._connection = pymysql.connect(**tls_kwargs)
                self._cursor = self._connection.cursor()

                if hasattr(self.connection, "configuration"):
                    self.connection.configuration = (
                        self.connection.configuration._replace(use_tls_enabled=True)
                    )
                logger.info(
                    "MySQL connection succeeded after enabling TLS automatically."
                )
            except Exception as e:
                logger.error(f"Failed to connect to MySQL: {e}")
                raise

            if self._cursor is not None:
                self.after_connect()

    def set_database(self, database: SQLDatabase) -> None:
        self.execute(f"USE {database.quoted_name}")

    def get_server_version(self) -> str:
        self.execute("SELECT VERSION() as version")
        version = self.cursor.fetchone()
        return version["version"]

    def get_server_uptime(self) -> Optional[int]:
        self.execute("SHOW STATUS LIKE 'Uptime'")
        result = self.fetchone()
        return int(result["Value"]) if result else None

    def get_databases(self) -> list[SQLDatabase]:
        self.execute("""
            SELECT
                isS.SCHEMA_NAME as database_name,
                isS.DEFAULT_COLLATION_NAME as default_collation,

                COUNT(DISTINCT CASE WHEN isT.TABLE_TYPE = 'BASE TABLE' THEN isT.TABLE_NAME END) AS total_tables,
                COUNT(DISTINCT CASE WHEN isT.TABLE_TYPE = 'VIEW' THEN isT.TABLE_NAME END) AS total_views,

                COALESCE(SUM(isT.DATA_LENGTH + isT.INDEX_LENGTH), 0) AS total_bytes,

                (SELECT COUNT(*) FROM information_schema.TRIGGERS isT WHERE isT.TRIGGER_SCHEMA = isS.SCHEMA_NAME) AS total_triggers,
                (SELECT COUNT(*) FROM information_schema.ROUTINES isR WHERE isR.ROUTINE_SCHEMA = isS.SCHEMA_NAME AND isR.ROUTINE_TYPE = 'PROCEDURE') AS total_procedures,
                (SELECT COUNT(*) FROM information_schema.ROUTINES isR WHERE isR.ROUTINE_SCHEMA = isS.SCHEMA_NAME AND isR.ROUTINE_TYPE = 'FUNCTION') AS total_functions,
                (SELECT COUNT(*) FROM information_schema.EVENTS isE WHERE isE.EVENT_SCHEMA = isS.SCHEMA_NAME) AS total_events
            FROM information_schema.SCHEMATA as isS
            LEFT JOIN information_schema.TABLES isT ON isT.TABLE_SCHEMA = isS.SCHEMA_NAME
            GROUP BY isS.SCHEMA_NAME, isS.DEFAULT_COLLATION_NAME
            ORDER BY isS.SCHEMA_NAME;
        """)
        results = []
        for i, row in enumerate(self.fetchall()):
            results.append(
                MySQLDatabase(
                    id=i,
                    name=row["database_name"],
                    default_collation=row["default_collation"],
                    total_bytes=float(row["total_bytes"]),
                    context=self,
                    get_tables_handler=self.get_tables,
                    get_procedures_handler=self.get_procedures,
                    get_views_handler=self.get_views,
                    get_triggers_handler=self.get_triggers,
                )
            )
        return results

    def get_procedures(self, database: SQLDatabase) -> list[MySQLProcedure]:
        results: list[MySQLProcedure] = []
        self.execute(
            f"""
            SELECT ROUTINE_NAME
            FROM INFORMATION_SCHEMA.ROUTINES
            WHERE ROUTINE_SCHEMA = '{database.name}' AND ROUTINE_TYPE = 'PROCEDURE'
            ORDER BY ROUTINE_NAME
            """
        )
        for i, result in enumerate(self.fetchall()):
            results.append(
                MySQLProcedure(
                    id=i,
                    name=result["ROUTINE_NAME"],
                    database=database,
                    parameters="",
                    statement="",
                )
            )

        return results

    def get_views(self, database: SQLDatabase):
        results: list[MySQLView] = []
        self.execute(
            f"SELECT TABLE_NAME, VIEW_DEFINITION FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{database.name}' ORDER BY TABLE_NAME"
        )
        for i, result in enumerate(self.fetchall()):
            results.append(
                MySQLView(
                    id=i,
                    name=result["TABLE_NAME"],
                    database=database,
                    statement=result["VIEW_DEFINITION"] or "",
                )
            )

        return results

    def get_definers(self) -> list[str]:
        self.execute("""
            SELECT DISTINCT CONCAT(User, '@', Host) as definer
            FROM mysql.user
            ORDER BY definer
        """)
        return [row["definer"] for row in self.fetchall()]

    def get_triggers(self, database: SQLDatabase) -> list[MySQLTrigger]:
        results: list[MySQLTrigger] = []
        self.execute(
            f"SELECT TRIGGER_NAME, ACTION_STATEMENT FROM INFORMATION_SCHEMA.TRIGGERS WHERE TRIGGER_SCHEMA = '{database.name}' ORDER BY TRIGGER_NAME"
        )
        for i, result in enumerate(self.fetchall()):
            results.append(
                MySQLTrigger(
                    id=i,
                    name=result["TRIGGER_NAME"],
                    database=database,
                    statement=result["ACTION_STATEMENT"],
                )
            )

        return results

    def get_tables(self, database: SQLDatabase) -> list[SQLTable]:
        logger.debug(f"get_tables for database={database.name}")

        QUERY_LOGS.append(f"/* get_tables for database={database.name} */")

        self.execute(f"""
            SELECT TABLE_NAME, ENGINE, TABLE_COLLATION, TABLE_ROWS, AUTO_INCREMENT,
            ROUND((DATA_LENGTH + INDEX_LENGTH), 2) as total_bytes
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = '{database.name}'
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)

        results = []
        for i, row in enumerate(self.cursor.fetchall()):
            results.append(
                MySQLTable(
                    id=i,
                    name=row["TABLE_NAME"],
                    database=database,
                    engine=row["ENGINE"],
                    collation_name=row["TABLE_COLLATION"],
                    auto_increment=int(row["AUTO_INCREMENT"] or 0),
                    total_bytes=row["total_bytes"],
                    total_rows=row["TABLE_ROWS"],
                    get_columns_handler=self.get_columns,
                    get_indexes_handler=self.get_indexes,
                    get_checks_handler=self.get_checks,
                    get_foreign_keys_handler=self.get_foreign_keys,
                    get_records_handler=self.get_records,
                )
            )

        return results

    def get_columns(self, table: SQLTable) -> list[SQLColumn]:
        results = []
        if table.id == -1:
            return results

        logger.debug(f"get_columns for table={table.name}")

        QUERY_LOGS.append(f"/* get_columns for table={table.name} */")

        self.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE,
                   IS_NULLABLE, COLUMN_DEFAULT, EXTRA, COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table.database.name}' AND TABLE_NAME = '{table.name}'
            ORDER BY ORDINAL_POSITION
        """)

        for i, row in enumerate(self.cursor.fetchall()):
            is_auto_increment = "auto_increment" in (row["EXTRA"] or "").lower()
            is_nullable = row["IS_NULLABLE"] == "YES"
            parse_type = self._parse_type(row["COLUMN_TYPE"])
            datatype = MySQLDataType.get_by_name(row["DATA_TYPE"])

            results.append(
                MySQLColumn(
                    id=i,
                    name=row["COLUMN_NAME"],
                    datatype=datatype,
                    is_nullable=is_nullable,
                    table=table,
                    server_default=row["COLUMN_DEFAULT"],
                    is_auto_increment=is_auto_increment,
                    length=parse_type.get("length"),
                    numeric_precision=parse_type.get("precision"),
                    numeric_scale=parse_type.get("scale"),
                    set=parse_type.get("set"),
                    is_unsigned=parse_type.get("is_unsigned", False),
                    is_zerofill=parse_type.get("is_zerofill", False),
                )
            )

        return results

    def get_indexes(self, table: SQLTable) -> list[SQLIndex]:
        if table is None or table.is_new:
            return []

        logger.debug(f"get_indexes for table={table.name}")

        QUERY_LOGS.append(f"/* get_indexes for table={table.name} */")

        results = []

        # Get primary key
        self.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{table.database.name}' AND TABLE_NAME = '{table.name}' AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """)
        pk_columns = [row["COLUMN_NAME"] for row in self.cursor.fetchall()]
        if pk_columns:
            results.append(
                MySQLIndex(
                    id=0,
                    name="PRIMARY KEY",
                    type=MySQLIndexType.PRIMARY,
                    columns=pk_columns,
                    table=table,
                )
            )

        # Get other indexes
        self.execute(f"""
            SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = '{table.database.name}' AND TABLE_NAME = '{table.name}' AND INDEX_NAME != 'PRIMARY'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """)
        index_data = {}
        for row in self.cursor.fetchall():
            idx_name = row["INDEX_NAME"]
            if idx_name not in index_data:
                index_data[idx_name] = {"columns": [], "unique": not row["NON_UNIQUE"]}
            index_data[idx_name]["columns"].append(row["COLUMN_NAME"])

        for i, (idx_name, data) in enumerate(index_data.items(), start=1):
            idx_type = MySQLIndexType.UNIQUE if data["unique"] else MySQLIndexType.INDEX
            results.append(
                MySQLIndex(
                    id=i,
                    name=idx_name,
                    type=idx_type,
                    columns=data["columns"],
                    table=table,
                )
            )

        return results

    def get_checks(self, table: MySQLTable) -> list["MySQLCheck"]:
        from structures.engines.mysql.database import MySQLCheck

        if table is None or table.is_new:
            return []

        query = f"""
            SELECT 
                cc.CONSTRAINT_NAME,
                cc.CHECK_CLAUSE
            FROM information_schema.CHECK_CONSTRAINTS cc
            JOIN information_schema.TABLE_CONSTRAINTS tc 
                ON cc.CONSTRAINT_SCHEMA = tc.CONSTRAINT_SCHEMA 
                AND cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = '{table.database.name}'
            AND tc.TABLE_NAME = '{table.name}'
            AND tc.CONSTRAINT_TYPE = 'CHECK'
            ORDER BY cc.CONSTRAINT_NAME
        """

        self.execute(query)
        rows = self.fetchall()

        results = []
        for i, row in enumerate(rows):
            results.append(
                MySQLCheck(
                    id=i,
                    name=row["CONSTRAINT_NAME"],
                    table=table,
                    expression=row["CHECK_CLAUSE"],
                )
            )

        return results

    def get_foreign_keys(self, table: SQLTable) -> list[SQLForeignKey]:
        if table is None or table.is_new:
            return []

        logger.debug(f"get_foreign_keys for table={table.name}")

        QUERY_LOGS.append(f"/* get_foreign_keys for table={table.name} */")

        self.execute(f"""
            SELECT
                isKcu.CONSTRAINT_NAME,
                GROUP_CONCAT(isKcu.COLUMN_NAME ORDER BY isKcu.ORDINAL_POSITION) as COLUMNS_NAMES,
                isKcu.REFERENCED_TABLE_NAME,
                GROUP_CONCAT(isKcu.REFERENCED_COLUMN_NAME ORDER BY ORDINAL_POSITION) as REFERENCED_COLUMNS,
                isRc.UPDATE_RULE,
                isRc.DELETE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE isKcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS isRc ON isRc.CONSTRAINT_NAME = isKcu.CONSTRAINT_NAME
            WHERE isKcu.TABLE_SCHEMA = '{table.database.name}' AND isKcu.TABLE_NAME = '{table.name}'
            GROUP BY CONSTRAINT_NAME, REFERENCED_TABLE_NAME, UPDATE_RULE, DELETE_RULE
        """)
        foreign_keys = []
        for i, row in enumerate(self.cursor.fetchall()):
            foreign_keys.append(
                MySQLForeignKey(
                    id=i,
                    name=row["CONSTRAINT_NAME"],
                    columns=row["COLUMNS_NAMES"].split(","),
                    table=table,
                    reference_table=row["REFERENCED_TABLE_NAME"],
                    reference_columns=row["REFERENCED_COLUMNS"].split(","),
                    on_update=row["UPDATE_RULE"],
                    on_delete=row["DELETE_RULE"],
                )
            )

        return foreign_keys

    def get_records(
        self,
        table: SQLTable,
        /,
        *,
        filters: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
        orders: Optional[str] = None,
    ) -> list[MySQLRecord]:
        QUERY_LOGS.append(f"/* get_records for table={table.name} */")
        if table is None or table.is_new:
            return []

        query = f"SELECT * FROM `{table.database.name}`.`{table.name}`"
        if filters:
            query += f" WHERE {filters}"
        if orders:
            query += f" ORDER BY {orders}"
        query += f" LIMIT {limit} OFFSET {offset}"
        self.execute(query)

        results = []
        for i, record in enumerate(self.cursor.fetchall(), start=offset):
            results.append(MySQLRecord(id=i, table=table, values=dict(record)))
        logger.debug(f"get records for table={table.name}")
        return results

    def build_empty_table(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> MySQLTable:
        id = MySQLContext.get_temporary_id(database.tables)

        if name is None:
            name = _(f"Table{str(id * -1):03}")

        default_values.setdefault("engine", "InnoDB")
        default_values.setdefault("collation_name", "utf8mb4_general_ci")

        return MySQLTable(
            id=id,
            name=name,
            database=database,
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_checks_handler=self.get_checks,
            get_foreign_keys_handler=self.get_foreign_keys,
            get_records_handler=self.get_records,
            **default_values,
        ).copy()

    def build_empty_column(
        self,
        table: SQLTable,
        datatype: SQLDataType,
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> MySQLColumn:
        id = MySQLContext.get_temporary_id(table.columns)

        if name is None:
            name = _(f"Column{str(id * -1):03}")

        return MySQLColumn(
            id=id, name=name, table=table, datatype=datatype, **default_values
        )

    def build_empty_index(
        self,
        table: MySQLTable,
        indextype: MySQLIndexType,
        columns: list[str],
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> MySQLIndex:
        id = MySQLContext.get_temporary_id(table.indexes)

        if name is None:
            name = _(f"Index{str(id * -1):03}")

        return MySQLIndex(
            id=id,
            name=name,
            type=indextype,
            columns=columns,
            table=table,
        )

    def build_empty_check(
        self,
        table: MySQLTable,
        /,
        name: Optional[str] = None,
        expression: Optional[str] = None,
        **default_values,
    ) -> "MySQLCheck":
        from structures.engines.mysql.database import MySQLCheck

        id = MySQLContext.get_temporary_id(table.checks)

        if name is None:
            name = f"check_{abs(id)}"

        return MySQLCheck(
            id=id, name=name, table=table, expression=expression or "", **default_values
        )

    def build_empty_foreign_key(
        self,
        table: MySQLTable,
        columns: list[str],
        /,
        name: Optional[str] = None,
        **default_values,
    ) -> MySQLForeignKey:
        id = MySQLContext.get_temporary_id(table.foreign_keys)

        if name is None:
            name = _(f"ForeignKey{str(id * -1):03}")

        reference_table = default_values.get("reference_table", "")
        reference_columns = default_values.get("reference_columns", [])

        return MySQLForeignKey(
            id=id,
            name=name,
            table=table,
            columns=columns,
            reference_table=reference_table,
            reference_columns=reference_columns,
            on_update=default_values.get("on_update", ""),
            on_delete=default_values.get("on_delete", ""),
        )

    def build_empty_record(
        self, table: MySQLTable, /, *, values: dict[str, Any]
    ) -> MySQLRecord:
        return MySQLRecord(
            id=MySQLContext.get_temporary_id(table.records), table=table, values=values
        )

    def build_empty_view(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> MySQLView:
        id = MySQLContext.get_temporary_id(database.views)

        if name is None:
            name = _(f"View{str(id * -1):03}")

        return MySQLView(
            id=id,
            name=name,
            database=database,
            statement=default_values.get("statement", ""),
        )

    def build_empty_function(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> "MySQLFunction":
        from structures.engines.mysql.database import MySQLFunction

        id = MySQLContext.get_temporary_id(database.functions)

        if name is None:
            name = f"function_{id}"

        return MySQLFunction(
            id=id,
            name=name,
            database=database,
            parameters=default_values.get("parameters", ""),
            returns=default_values.get("returns", "INT"),
            deterministic=default_values.get("deterministic", False),
            sql=default_values.get("sql", ""),
        )

    def build_empty_procedure(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> MySQLProcedure:
        id = MySQLContext.get_temporary_id(database.procedures)

        if name is None:
            name = f"procedure_{id}"

        return MySQLProcedure(
            id=id,
            name=name,
            database=database,
            parameters=default_values.get("parameters", ""),
            statement=default_values.get("statement", ""),
        )

    def build_empty_trigger(
        self, database: SQLDatabase, /, name: Optional[str] = None, **default_values
    ) -> MySQLTrigger:
        id = MySQLContext.get_temporary_id(database.triggers)

        if name is None:
            name = f"trigger_{id}"

        return MySQLTrigger(
            id=id,
            name=name,
            database=database,
            statement=default_values.get("statement", ""),
        )
