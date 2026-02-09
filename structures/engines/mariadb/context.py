import re

from typing import Any, Optional
from gettext import gettext as _

import pymysql

from helpers.logger import logger
from structures.connection import Connection

from structures.engines.context import QUERY_LOGS, AbstractContext
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLTrigger
from structures.engines.datatype import SQLDataType
from structures.engines.mariadb import MAP_COLUMN_FIELDS
from structures.engines.mariadb.database import MariaDBTable, MariaDBColumn, MariaDBIndex, MariaDBForeignKey, MariaDBRecord, MariaDBView, MariaDBTrigger, MariaDBDatabase
from structures.engines.mariadb.datatype import MariaDBDataType
from structures.engines.mariadb.indextype import MariaDBIndexType


class MariaDBContext(AbstractContext):
    MAP_COLUMN_FIELDS = MAP_COLUMN_FIELDS

    DATATYPE = MariaDBDataType
    INDEXTYPE = MariaDBIndexType

    QUOTE_IDENTIFIER = "`"

    def __init__(self, connection: Connection):
        super().__init__(connection)

        self.host = connection.configuration.hostname
        self.user = connection.configuration.username
        self.password = connection.configuration.password
        # self.database = session.configuration.database
        self.port = getattr(connection.configuration, 'port', 3306)

    def _on_connect(self, *args, **kwargs):
        super()._on_connect(*args, **kwargs)
        self.execute("""
            SELECT COLLATION_NAME, CHARACTER_SET_NAME FROM information_schema.COLLATIONS
            WHERE CHARACTER_SET_NAME IS NOT NULL
            ORDER BY CHARACTER_SET_NAME, COLLATION_NAME;
        """)
        for row in self.fetchall():
            self.COLLATIONS[row['COLLATION_NAME']] = row['CHARACTER_SET_NAME']

        self.execute("""SHOW ENGINES;""")
        self.ENGINES = [dict(row).get("Engine") for row in self.fetchall()]

        self.execute("""
            SELECT WORD FROM information_schema.KEYWORDS
            ORDER BY WORD;
        """)
        self.KEYWORDS = tuple(row["WORD"] for row in self.fetchall())

        self.execute("""
            SELECT FUNCTION FROM information_schema.SQL_FUNCTIONS
            ORDER BY FUNCTION;
        """)
        builtin_functions = tuple(row["FUNCTION"] for row in self.fetchall())

        self.execute("""
            SELECT DISTINCT ROUTINE_NAME FROM information_schema.ROUTINES
            WHERE ROUTINE_TYPE = 'FUNCTION'
            ORDER BY ROUTINE_NAME;
        """)
        user_functions = tuple(row["ROUTINE_NAME"] for row in self.fetchall())

        self.FUNCTIONS = builtin_functions + user_functions

    def _parse_type(self, column_type: str):
        types = MariaDBDataType.get_all()
        type_set = [x.lower() for type in types if type.has_set for x in ([type.name] + type.alias)]
        type_length = [x.lower() for type in types if type.has_length for x in ([type.name] + type.alias)]

        if match := re.search(fr"^({'|'.join(type_set)})\((.*)\)$", column_type):
            return dict(
                name=match.group(1).upper(),
                set=[value.strip("'") for value in match.group(2).split(",")]
            )
        elif match := re.search(fr"^({'|'.join(type_length)})\((.*)\)$", column_type):
            return dict(
                name=match.group(1).upper(),
                length=int(match.group(2))
            )

        elif match := re.search(r'(\w+)\s*\((\d+)(?:,\s*(\d+))?\)(\s*unsigned)?(\s*zerofill)?', column_type):
            return dict(
                name=match.group(1).upper(),
                precision=int(match.group(2)),
                scale=int(match.group(3)) if match.group(3) else None,
                is_unsigned=bool(match.group(4)),
                is_zerofill=bool(match.group(5))
            )

        return dict()

    def connect(self, **connect_kwargs) -> None:
        if self._connection is None:
            try:
                self._connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    # database=self.database,
                    cursorclass=pymysql.cursors.DictCursor,
                    port=self.port,
                    **connect_kwargs
                )
                self._cursor = self._connection.cursor()
            except Exception as e:
                logger.error(f"Failed to connect to MariaDB: {e}", exc_info=True)
                raise
            else:
                self._on_connect()

    def get_server_version(self) -> str:
        self.execute("SELECT VERSION() as version")
        version = self.cursor.fetchone()
        return version["version"]

    def get_server_uptime(self) -> Optional[int]:
        self.execute("SHOW STATUS LIKE 'Uptime'")
        result = self.fetchone()
        return int(result['Value']) if result else None

    def get_databases(self) -> list[SQLDatabase]:
        self.execute("""
                    SELECT
                        isS.SCHEMA_NAME as database_name,
                        isS.DEFAULT_COLLATION_NAME as default_collation,
                        COALESCE(SUM(isT.DATA_LENGTH + isT.INDEX_LENGTH), 0) AS total_bytes
                    FROM information_schema.SCHEMATA as isS
                    LEFT JOIN information_schema.TABLES isT ON isT.TABLE_SCHEMA = isS.SCHEMA_NAME
                    GROUP BY isS.SCHEMA_NAME, isS.DEFAULT_COLLATION_NAME
                    ORDER BY isS.SCHEMA_NAME;
                """)
        results = []
        for i, row in enumerate(self.fetchall()):
            results.append(MariaDBDatabase(
                id=i,
                name=row["database_name"],
                default_collation=row["default_collation"],
                total_bytes=float(row["total_bytes"]),
                context=self,
                get_tables_handler=self.get_tables,
                get_views_handler=self.get_views,
                get_triggers_handler=self.get_triggers,
            ))
        return results

    def get_views(self, database: SQLDatabase):
        results: list[MariaDBView] = []
        self.execute(f"SELECT TABLE_NAME, VIEW_DEFINITION FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{database.name}' ORDER BY TABLE_NAME")
        for i, result in enumerate(self.fetchall()):
            results.append(MariaDBView(
                id=i,
                name=result['TABLE_NAME'],
                database=database,
                sql=result['VIEW_DEFINITION']
            ))

        return results

    def get_triggers(self, database: SQLDatabase) -> list[MariaDBTrigger]:
        results: list[MariaDBTrigger] = []
        self.execute(f"SELECT TRIGGER_NAME, ACTION_STATEMENT FROM INFORMATION_SCHEMA.TRIGGERS WHERE TRIGGER_SCHEMA = '{database.name}' ORDER BY TRIGGER_NAME")
        for i, result in enumerate(self.fetchall()):
            results.append(MariaDBTrigger(
                id=i,
                name=result['TRIGGER_NAME'],
                database=database,
                sql=result['ACTION_STATEMENT']
            ))

        return results

    def get_tables(self, database: SQLDatabase) -> list[SQLTable]:
        QUERY_LOGS.append(f"/* get_tables for database={database.name} */")

        self.execute(f"""
            SELECT TABLE_NAME, ENGINE, TABLE_COLLATION, TABLE_ROWS, AUTO_INCREMENT,
            CREATE_TIME, UPDATE_TIME, ROUND(DATA_LENGTH + INDEX_LENGTH, 2) as total_bytes
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = '{database.name}'
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)

        results = []
        for i, row in enumerate(self.fetchall()):
            results.append(
                MariaDBTable(
                    id=i,
                    name=row['TABLE_NAME'],
                    database=database,
                    engine=row['ENGINE'],
                    collation_name=row['TABLE_COLLATION'],
                    auto_increment=int(row['AUTO_INCREMENT'] or 0),
                    total_bytes=row['total_bytes'],
                    total_rows=row["TABLE_ROWS"],
                    created_at=row['CREATE_TIME'],
                    updated_at=row['UPDATE_TIME'],
                    get_columns_handler=self.get_columns,
                    get_indexes_handler=self.get_indexes,
                    get_foreign_keys_handler=self.get_foreign_keys,
                    get_records_handler=self.get_records,
                )
            )

        return results

    def get_columns(self, table: SQLTable) -> list[SQLColumn]:
        results = []
        if table.id == -1:
            return results

        QUERY_LOGS.append(f"/* get_columns for table={table.name} */")

        self.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE,
                   IS_NULLABLE, COLUMN_DEFAULT, EXTRA, COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table.database.name}' AND TABLE_NAME = '{table.name}'
            ORDER BY ORDINAL_POSITION
        """)

        for i, row in enumerate(self.cursor.fetchall()):
            is_auto_increment = 'auto_increment' in (row['EXTRA'] or '').lower()
            is_nullable = row['IS_NULLABLE'] == 'YES'
            parse_type = self._parse_type(row['COLUMN_TYPE'])
            datatype = MariaDBDataType.get_by_name(row['DATA_TYPE'])

            results.append(
                MariaDBColumn(
                    id=i,
                    name=row['COLUMN_NAME'],
                    datatype=datatype,
                    is_nullable=is_nullable,
                    table=table,
                    server_default=row['COLUMN_DEFAULT'],
                    is_auto_increment=is_auto_increment,
                    length=parse_type.get('length'),
                    numeric_precision=parse_type.get('precision'),
                    numeric_scale=parse_type.get('scale'),
                    set=parse_type.get('set'),
                    is_unsigned=parse_type.get('is_unsigned', False),
                    is_zerofill=parse_type.get('is_zerofill', False),
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
        pk_columns = [row['COLUMN_NAME'] for row in self.cursor.fetchall()]
        if pk_columns:
            results.append(
                MariaDBIndex(
                    id=0,
                    name="PRIMARY KEY",
                    type=MariaDBIndexType.PRIMARY,
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
            idx_name = row['INDEX_NAME']
            if idx_name not in index_data:
                index_data[idx_name] = {'columns': [], 'unique': not row['NON_UNIQUE']}
            index_data[idx_name]['columns'].append(row['COLUMN_NAME'])

        for i, (idx_name, data) in enumerate(index_data.items(), start=1):
            idx_type = MariaDBIndexType.UNIQUE if data['unique'] else MariaDBIndexType.INDEX
            results.append(
                MariaDBIndex(
                    id=i,
                    name=idx_name,
                    type=idx_type,
                    columns=data['columns'],
                    table=table,
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
                kcu.CONSTRAINT_NAME,
                GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION) as COLUMNS_NAME,
                kcu.REFERENCED_TABLE_NAME,
                GROUP_CONCAT(REFERENCED_COLUMN_NAME ORDER BY ORDINAL_POSITION) as REFERENCED_COLUMNS,
                UPDATE_RULE,
                DELETE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            WHERE kcu.TABLE_SCHEMA = '{table.database.name}' AND kcu.TABLE_NAME = '{table.name}'
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            GROUP BY CONSTRAINT_NAME
        """)
        foreign_keys = []
        for i, row in enumerate(self.cursor.fetchall()):
            foreign_keys.append(MariaDBForeignKey(
                id=i,
                name=row['CONSTRAINT_NAME'],
                columns=row["COLUMNS_NAME"].split(","),
                table=table,
                reference_table=row['REFERENCED_TABLE_NAME'],
                reference_columns=row["REFERENCED_COLUMNS"].split(","),
                on_update=row['UPDATE_RULE'],
                on_delete=row['DELETE_RULE'],
            ))

        return foreign_keys

    def get_records(self, table: SQLTable, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None) -> list[MariaDBRecord]:
        results = []
        for i, record in enumerate(super().get_records(table, filters, limit, offset, orders), start=offset):
            results.append(
                MariaDBRecord(id=i, table=table, values=dict(record))
            )

        return results

    def build_empty_table(self, database: SQLDatabase) -> MariaDBTable:
        return MariaDBTable(
            id=MariaDBContext.get_temporary_id(database.tables),
            name='',
            database=database,
            engine='mariadb',
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_foreign_keys_handler=self.get_foreign_keys,
            get_records_handler=self.get_records,
        ).copy()

    def build_empty_column(self, table: SQLTable, datatype: SQLDataType, **default_values) -> MariaDBColumn:
        id = MariaDBContext.get_temporary_id(table.columns)
        return MariaDBColumn(
            id=id,
            name=_(f"Column{str(id * -1):0>3}"),
            table=table,
            datatype=datatype,
            **default_values
        )

    def build_empty_index(self, name: str, type: MariaDBIndexType, table: MariaDBTable, columns: list[str]) -> MariaDBIndex:
        return MariaDBIndex(
            id=MariaDBContext.get_temporary_id(table.indexes),
            name=name,
            type=type,
            columns=columns,
            table=table,
        )

    def build_empty_foreign_key(self, name: str, table: MariaDBTable, columns: list[str]) -> MariaDBForeignKey:
        return MariaDBForeignKey(
            id=MariaDBContext.get_temporary_id(table.foreign_keys),
            name=name,
            table=table,
            columns=columns,
            reference_table="",
            reference_columns=[],
            on_update="",
            on_delete=""
        )

    def build_empty_record(self, table: MariaDBTable, values: dict[str, Any]) -> MariaDBRecord:
        return MariaDBRecord(
            id=MariaDBContext.get_temporary_id(table.records),
            table=table,
            values=values
        )
