import re
import sqlite3
from collections import defaultdict
from typing import Optional, List, Dict, Any

from gettext import gettext as _

from helpers.logger import logger

from structures.engines.context import QUERY_LOGS, AbstractContext
from structures.engines.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLTrigger
from structures.engines.datatype import SQLDataType
from structures.engines.indextype import SQLIndexType

from structures.engines.sqlite import COLLATIONS, MAP_COLUMN_FIELDS, COLUMNS_PATTERN, COLUMN_ATTRIBUTES_PATTERN, TABLE_CONSTRAINTS_PATTERN
from structures.engines.sqlite.database import SQLiteTable, SQLiteColumn, SQLiteIndex, SQLiteForeignKey, SQLiteRecord, SQLiteView, SQLiteTrigger, SQLiteDatabase, SQLiteCheck
from structures.engines.sqlite.datatype import SQLiteDataType
from structures.engines.sqlite.indextype import SQLiteIndexType


class SQLiteContext(AbstractContext):
    ENGINES = ["default"]
    COLLATIONS = COLLATIONS
    MAP_COLUMN_FIELDS = MAP_COLUMN_FIELDS

    DATATYPE = SQLiteDataType()
    INDEXTYPE = SQLiteIndexType()

    _map_sqlite_master = defaultdict(lambda: defaultdict(dict))

    def __init__(self, session):
        super().__init__(session)

        self.filename = session.configuration.filename

    def _on_connect(self, *args, **kwargs):
        super()._on_connect(*args, **kwargs)
        self.execute("PRAGMA database_list;")
        self.execute("PRAGMA foreign_keys = ON;")
        # self.execute("PRAGMA case_sensitive_like = ON")
        # self.execute("PRAGMA secure_delete = ON")
        # self.execute("PRAGMA auto_vacuum = FULL")
        # self.execute("PRAGMA cache_size = 10000")
        # self.execute("PRAGMA journal_mode = WAL")
        self.execute("PRAGMA temp_store = MEMORY;")
        # self.execute("PRAGMA threads = 4")
        # self.execute("PRAGMA page_size = 4096")

    def connect(self, **connect_kwargs) -> None:
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(self.filename)
                self._connection.row_factory = sqlite3.Row
                self._cursor = self._connection.cursor()
                self._on_connect()
            except Exception as e:
                logger.error(f"Failed to connect to SQLite: {e}")
                raise

    def get_server_version(self) -> str:
        self.execute("SELECT sqlite_version()")
        version = self.cursor.fetchone()
        return version[0]

    def get_server_uptime(self) -> Optional[int]:
        return None

    def get_databases(self) -> List[SQLDatabase]:
        self.execute("SELECT * from sqlite_master ORDER BY name")
        for i, result in enumerate(self.fetchall()):
            self._map_sqlite_master[result['tbl_name']][result['type']][result['name']] = result['sql']

        self.execute("SELECT page_count * page_size as total_bytes FROM pragma_page_count(), pragma_page_size();")

        return [SQLiteDatabase(
            id=0,
            name='main',
            context=self,
            total_bytes=float(self.fetchone()['total_bytes']),
            get_tables_handler=self.get_tables,
            get_views_handler=self.get_views,
            get_triggers_handler=self.get_triggers,
        )]

    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        QUERY_LOGS.append(f"/* get_tables for database={database.name} */")

        has_sqlite_sequence = False

        self.execute(""" SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence'; """)
        if self.fetchone():
            has_sqlite_sequence = True

        selects = [
            "sM.*",
            "SUM(dbS.pgsize) AS total_bytes",
            "SUM(dbS.ncell) AS total_rows",
        ]
        if has_sqlite_sequence:
            selects.append("IFNULL(sS.seq, 0) AS autoincrement_value")
        else:
            selects.append("0 AS autoincrement_value")

        self.execute(f"""
            SELECT {', '.join(selects)}
            FROM sqlite_master as sM
            JOIN dbstat As dbS ON dbS.name = sM.name
            {f"LEFT JOIN sqlite_sequence as sS ON sS.name = sM.tbl_name" if has_sqlite_sequence else ""}
            WHERE sM.name NOT LIKE 'sqlite_%'
            GROUP BY sM.tbl_name
            ORDER BY sM.tbl_name;
        """)

        results = []
        for i, row in enumerate(self.fetchall()):
            if row['type'] == 'table':
                results.append(
                    SQLiteTable(
                        id=i,
                        name=row['tbl_name'],
                        database=database,
                        engine='default',
                        auto_increment=int(row["autoincrement_value"]),
                        total_bytes=row['total_bytes'],
                        total_rows=row["total_rows"],
                        collation_name="BINARY",
                        get_columns_handler=self.get_columns,
                        get_indexes_handler=self.get_indexes,
                        get_checks_handler=self.get_checks,
                        get_foreign_keys_handler=self.get_foreign_keys,
                        get_records_handler=self.get_records,
                    )
                )

        return results

    def get_columns(self, table: SQLiteTable) -> List[SQLColumn]:
        results = []
        if table is None or table.is_new:
            return results

        if not (table_match := re.search(r"""CREATE\s+TABLE\s+(?:[`'"]?\w+[`'"]?\s+)?\((?P<columns>.*)\)""", self._map_sqlite_master[table.name]["table"][table.name], re.IGNORECASE | re.DOTALL)):
            return results

        table_group_dict = table_match.groupdict()

        columns = re.sub(r'\s*--\s*.*', '', table_group_dict['columns'])

        columns_matches = re.findall(r'([^,(]+(?:\([^)]*\)[^,(]*)*)(?:\s*,\s*|$)', columns, re.DOTALL)

        columns = [re.sub(r'\s+', ' ', match).strip().rstrip(',') for match in columns_matches if match.strip()]

        for i, column in enumerate(columns):
            is_special_syntax = False

            for prefix in ["PRIMARY KEY", "UNIQUE", "FOREIGN KEY"]:
                if re.match(f"^{re.escape(prefix)}", column, re.IGNORECASE):
                    is_special_syntax = True
                    break

            for prefix in ["CONSTRAINT", "CHECK"]:
                if re.match(f"^{re.escape(prefix)}", column[:len(prefix)], re.IGNORECASE):
                    self._map_sqlite_master[table.name]["constraints"].setdefault(prefix, []).append(column)
                    is_special_syntax = True
                    break

            if is_special_syntax:
                continue

            if not (columns_match := COLUMNS_PATTERN.match(column)):
                continue

            column_dict = columns_match.groupdict()

            attributes_str = column_dict.pop('attributes').strip()
            attr_dict = {}
            for pattern in COLUMN_ATTRIBUTES_PATTERN:
                if m := pattern.search(attributes_str):
                    attr_dict.update({k: v for k, v in m.groupdict().items() if v is not None})
            column_dict.update(attr_dict)

            results.append(
                SQLiteColumn(
                    id=i,
                    name=column_dict["name"],
                    datatype=SQLiteDataType.get_by_name(column_dict['datatype']),
                    is_nullable=column_dict.get('is_nullable', "NULL") == "NULL",
                    table=table,
                    server_default=column_dict.get('default'),
                    is_auto_increment=column_dict.get("is_auto_increment") == "AUTOINCREMENT",
                    length=column_dict['length'],
                    numeric_precision=column_dict['precision'],
                    numeric_scale=column_dict['scale'],
                    virtuality=column_dict.get('virtuality'),
                    expression=column_dict.get('expression'),
                    collation_name=column_dict.get('collate'),
                    check=column_dict.get('check'),
                )
            )

        return results

    def get_checks(self, table: SQLiteTable) -> List[SQLiteCheck]:
        results = []
        if table is None or table.is_new:
            return results

        for type, constraints in self._map_sqlite_master[table.name]["constraints"].items():
            
            for i, constraint in enumerate(constraints) :
                if not TABLE_CONSTRAINTS_PATTERN.get(type) :
                    continue

                if constraint_column := re.search( TABLE_CONSTRAINTS_PATTERN[type].pattern, constraint, re.IGNORECASE | re.DOTALL):
                    constraint_column_dict = constraint_column.groupdict()
                    results.append(
                        SQLiteCheck(
                            id=i,
                            name=constraint_column_dict.get("constraint_name"),
                            table=table,
                            expression=constraint_column_dict.get("check")
                        )
                    )


        return results

    def get_indexes(self, table: SQLiteTable) -> List[SQLIndex]:
        if table is None or table.is_new:
            return []
        logger.debug(f"get_indexes for table={table.name}")

        QUERY_LOGS.append(f"/* get_indexes for table={table.name} */")

        results = []

        self.execute(f"SELECT * FROM pragma_table_info('{table.name}') WHERE pk != 0 ORDER BY pk;")
        if (pk_index := self.fetchall()) and len(pk_index):
            results.append(
                SQLiteIndex(
                    id=0,
                    name="PRIMARY KEY",
                    type=SQLiteIndexType.PRIMARY,
                    columns=[col['name'] for col in pk_index],
                    table=table,
                )
            )

        self.execute(f"SELECT * FROM pragma_index_list('{table.name}') WHERE `origin` != 'pk' order by seq desc;")

        for idx in [dict(row) for row in self.cursor.fetchall()]:
            id = int(idx['seq']) + 1
            name = idx['name']
            is_unique = bool(idx.get('unique', False))
            is_partial = bool(idx.get('partial', False))

            self.execute(f"SELECT * FROM pragma_index_info('{name}');")
            pragma_index_info = self.fetchone()

            is_expression = True if pragma_index_info['cid'] == -2 else False

            columns = []
            condition = ""

            if name.startswith("sqlite_"):
                columns = [pragma_index_info['name']]
            else:
                sql = self._map_sqlite_master[table.name]["index"][name]

                if search := re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+\w+\s*\((?P<columns>(?:[^()]+|\([^()]*\))+)\)(?:\s+WHERE\s+(?P<conditions>.+))?', sql, re.IGNORECASE | re.DOTALL):
                    groups = search.groupdict()

                    columns = groups['columns'].strip().split(',')
                    condition = groups.get('conditions', [])

            # Determine index type
            index_type = SQLiteIndexType.INDEX

            if is_unique:
                index_type = SQLiteIndexType.UNIQUE
            elif is_partial:
                index_type = SQLiteIndexType.PARTIAL
            elif is_expression:
                index_type = SQLiteIndexType.EXPRESSION

            results.append(
                SQLiteIndex(
                    id=id,
                    name=name,
                    type=index_type,
                    columns=columns,
                    condition=condition,
                    table=table,
                )
            )

        type_order = {t: i for i, t in enumerate(SQLiteIndexType.get_all())}
        results.sort(key=lambda idx: type_order.get(idx.type, 999))

        return results

    def get_foreign_keys(self, table: SQLiteTable) -> List[SQLForeignKey]:
        if table is None or table.is_new:
            return []
        logger.debug(f"get_foreign_keys for table={table.name}")

        QUERY_LOGS.append(f"/* get_foreign_keys for table={table.name} */")

        self.execute(f"SELECT"
                     f" `id`, `table`, GROUP_CONCAT(`from`) as `from`, GROUP_CONCAT(`to`) as `to`, `on_update`, `on_delete`"
                     f" FROM pragma_foreign_key_list('{table.name}') GROUP BY id;")

        foreign_keys = []
        for fk in [dict(row) for row in self.fetchall()]:
            id = fk['id']
            columns = fk['from'].split(",")
            reference_columns = fk['to'].split(",")
            name = f"""fk_{table.name}_{'_'.join(columns)}-{fk['table']}_{'_'.join(reference_columns)}_{id}"""

            foreign_keys.append(
                SQLiteForeignKey(
                    id=int(id),
                    name=name,
                    table=table,
                    columns=columns,
                    reference_table=fk['table'],
                    reference_columns=reference_columns,
                    on_update=fk.get('on_update', ''),
                    on_delete=fk.get('on_delete', ''),
                )
            )

        return foreign_keys

    def get_records(self, table: SQLiteTable, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None) -> List[SQLiteRecord]:
        QUERY_LOGS.append(f"/* get_records for table={table.name} */")
        if table is None or table.is_new:
            return []

        query = f"SELECT * FROM `{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)

        results = []
        for i, record in enumerate(self.cursor.fetchall(), start=offset):
            results.append(
                SQLiteRecord(id=i, table=table, values=dict(record))
            )
        logger.debug(f"get records for table={table.name}")
        return results

    def get_views(self, database: SQLDatabase):
        results: List[SQLiteView] = []
        self.execute("SELECT * FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        for i, result in enumerate(self.fetchall()):
            results.append(SQLiteView(
                id=i,
                name=result['name'],
                database=database,
                sql=result['sql']
            ))

        return results

    def get_triggers(self, database: SQLDatabase) -> List[SQLiteTrigger]:
        results: List[SQLiteTrigger] = []
        self.execute("SELECT * FROM sqlite_master WHERE type='trigger' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        for i, result in enumerate(self.fetchall()):
            results.append(SQLiteTrigger(
                id=i,
                name=result['name'],
                database=database,
                sql=result['sql']
            ))

        return results

    def build_empty_table(self, database: SQLDatabase) -> SQLiteTable:
        return SQLiteTable(
            id=SQLiteContext.get_temporary_id(database.tables),
            name='',
            database=database,
            engine='sqlite',
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_foreign_keys_handler=self.get_foreign_keys,
            get_records_handler=self.get_records,
        )

    def build_empty_column(self, table: SQLiteTable, datatype: SQLDataType, **default_values) -> SQLiteColumn:
        id = SQLiteContext.get_temporary_id(table.columns)

        return SQLiteColumn(
            id=id,
            name=_(f"Column{str(id * -1):03}"),
            table=table,
            datatype=datatype,
            **default_values
        )

    def build_empty_index(self, name: str, table: SQLiteTable, type: SQLIndexType, columns: List[str]) -> SQLiteIndex:
        return SQLiteIndex(
            id=SQLiteContext.get_temporary_id(table.indexes),
            name=name,
            type=type,
            columns=columns,
            table=table,
        )

    def build_empty_foreign_key(self, name: str, table: SQLiteTable, columns: List[str]) -> SQLiteForeignKey:
        return SQLiteForeignKey(
            id=SQLiteContext.get_temporary_id(table.foreign_keys),
            name=name,
            table=table,
            columns=columns,
            reference_table="",
            reference_columns=[],
            on_update="",
            on_delete=""
        )

    def build_empty_record(self, table: SQLiteTable, values: Dict[str, Any]) -> SQLiteRecord:
        return SQLiteRecord(
            id=SQLiteContext.get_temporary_id(table.records),
            table=table,
            values=values
        )
