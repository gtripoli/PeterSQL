import re
import sqlite3
from typing import Optional, List, Dict, Any

from helpers.logger import logger

from engines.structures.context import LOG_QUERY, AbstractContext
from engines.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLTrigger
from engines.structures.datatype import SQLDataType

from engines.structures.sqlite import COLLATIONS, MAP_COLUMN_FIELDS, COLUMNS_PATTERN, ATTRIBUTES_PATTERN
from engines.structures.sqlite.database import SQLiteTable, SQLiteColumn, SQLiteIndex, SQLiteForeignKey, SQLiteRecord, SQLiteView, SQLiteTrigger
from engines.structures.sqlite.datatype import SQLiteDataType
from engines.structures.sqlite.indextype import SQLiteIndexType


class SQLiteContext(AbstractContext):
    COLLATIONS = COLLATIONS
    MAP_COLUMN_FIELDS = MAP_COLUMN_FIELDS

    def __init__(self, session):
        self.filename = session.configuration.filename

        self.connection_url = f"sqlite:///{self.filename}"

        super().__init__(self.connection_url)

    def _on_connect(self, *args, **kwargs):
        super()._on_connect(*args, **kwargs)
        self.execute("PRAGMA foreign_keys = ON")
        # self.execute("PRAGMA case_sensitive_like = ON")
        # self.execute("PRAGMA secure_delete = ON")
        # self.execute("PRAGMA auto_vacuum = FULL")
        # self.execute("PRAGMA cache_size = 10000")
        # self.execute("PRAGMA journal_mode = WAL")
        self.execute("PRAGMA temp_store = MEMORY")
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
        return [SQLDatabase(
            id=0,
            name='main',
            context=self,
            get_tables_handler=self.get_tables,
            get_views_handler=self.get_views,
            get_triggers_handler=self.get_triggers,
        )]

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

    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        # self.execute("SELECT * FROM sqlite_master WHERE type IN('table', 'view', 'trigger') AND name NOT LIKE 'sqlite_%' ORDER BY name")
        LOG_QUERY.append(f"/* get_tables for database={database.name} */")

        self.execute("SELECT * FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")

        results = []
        for i, row in enumerate(self.cursor.fetchall()):
            results.append(
                SQLiteTable(
                    id=i,
                    name=row['name'],
                    database=database,
                    engine='sqlite',
                    get_columns_handler=self.get_columns,
                    get_indexes_handler=self.get_indexes,
                    get_foreign_keys_handler=self.get_foreign_keys,
                    get_records_handler=self.get_records,
                )
            )

        return results

    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        results = []
        if table.id == -1:
            return results

        LOG_QUERY.append(f"/* get_columns for table={table.name} */")

        self.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table.name}'")
        if not (sql_table_result := self.cursor.fetchone()):
            return results

        sql_create_table = sql_table_result['sql']

        if not (table_match := re.search(r"""CREATE\s+TABLE\s+(?:[`'"]?\w+[`'"]?\s+)?\((?P<columns>.*)\)""", sql_create_table, re.IGNORECASE | re.DOTALL)):
            return results

        table_match = table_match.groupdict()

        columns = re.sub(r'\s*--\s*.*', '', table_match['columns'])

        columns = re.split(r',\W+', columns)

        columns = [re.sub(r"\s{2,}|\n+", ' ', c).strip() for c in columns]

        for i, column in enumerate(columns):
            if not (columns_match := COLUMNS_PATTERN.match(column)):
                continue

            if column.startswith("PRIMARY KEY") or column.startswith("UNIQUE") or column.startswith("FOREIGN KEY"):
                continue

            column_dict = columns_match.groupdict()

            attributes_str = column_dict.pop('attributes').strip()
            attr_dict = {}
            for pattern in ATTRIBUTES_PATTERN:
                if m := pattern.search(attributes_str):
                    attr_dict.update({k: v for k, v in m.groupdict().items() if v is not None})
            column_dict.update(attr_dict)

            results.append(
                SQLiteColumn(
                    id=i,
                    pos=i + 1,
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

    def get_indexes(self, table: SQLTable) -> List[SQLIndex]:
        if table.id == -1:
            return []
        logger.debug(f"get_indexes for table={table.name}")

        LOG_QUERY.append(f"/* get_indexes for table={table.name} */")

        results = []

        self.execute(f"SELECT * FROM pragma_table_info('{table.name}') WHERE pk != 0 ORDER BY pk;")
        pk_index = self.cursor.fetchall()
        if len(pk_index):
            results.append(
                SQLiteIndex(
                    id=0,
                    pos=0 + 1,
                    name="PRIMARY KEY",
                    type=SQLiteIndexType.PRIMARY,
                    columns=[col['name'] for col in pk_index],
                    table=table,
                )
            )

        self.execute(f"SELECT * FROM pragma_index_list('{table.name}') WHERE `origin` != 'pk' order by seq desc;")
        indexes = [dict(row) for row in self.cursor.fetchall()]

        for idx in indexes:
            id = int(idx['seq']) + 1
            name = idx['name']
            is_unique = bool(idx.get('unique', False))
            is_partial = bool(idx.get('partial', False))
            # is_primary = bool(idx.get('primary', idx.get('origin') == 'pk'))
            # origin = idx.get('origin', '')
            is_expression = False

            self.execute(f"SELECT * FROM pragma_index_info('{name}');")
            index_info = self.cursor.fetchall()

            columns = []
            condition = ""
            expression = []

            for row in index_info:
                if row['cid'] == -2:
                    is_expression = True
                else:
                    columns.append(row['name'])

            if is_expression or is_partial:
                self.execute(f"SELECT sql FROM sqlite_master WHERE `tbl_name` = '{table.name}' AND `name` = '{name}';")
                sql_row = self.cursor.fetchone()
                sql = sql_row['sql'] if sql_row else None

                if groups := re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+\w+\s*\((?P<columns>(?:[^()]+|\([^()]*\))+)\)(?:\s+WHERE\s+(?P<condition>.+))?', sql, re.IGNORECASE | re.DOTALL).groupdict():
                    if is_partial:
                        columns = groups['columns'].strip().split(',')
                    else:
                        expression = groups['columns'].strip().split(',')

                    condition = groups.get('condition', None)

            # Determine index type
            index_type = SQLiteIndexType.NORMAL

            if is_unique:
                index_type = SQLiteIndexType.UNIQUE
            elif is_partial:
                index_type = SQLiteIndexType.PARTIAL
            elif is_expression:
                index_type = SQLiteIndexType.EXPRESSION

            results.append(
                SQLiteIndex(
                    id=id,
                    pos=id + 1,
                    name=name,
                    type=index_type,
                    columns=columns,
                    condition=condition,
                    expression=expression,
                    table=table,
                )
            )

        type_order = {t: i for i, t in enumerate(SQLiteIndexType.get_all())}
        results.sort(key=lambda idx: type_order.get(idx.type, 999))

        return results

    def get_foreign_keys(self, table: SQLTable) -> List[SQLForeignKey]:
        if table.id == -1:
            return []
        logger.debug(f"get_foreign_keys for table={table.name}")

        LOG_QUERY.append(f"/* get_foreign_keys for table={table.name} */")

        self.execute(f"SELECT"
                     f" `id`, `table`, GROUP_CONCAT(`from`) as `from`, GROUP_CONCAT(`to`) as `to`, `on_update`, `on_delete`"
                     f" FROM pragma_foreign_key_list('{table.name}') GROUP BY id;")
        foreign_keys = [dict(row) for row in self.cursor.fetchall()]

        results = []
        for fk in foreign_keys:
            id = fk['id']
            name = f"fk_{table.name}_{fk['table']}_{id}"

            columns = fk['from'].split(",")
            reference_columns = fk['to'].split(",")

            results.append(
                SQLiteForeignKey(
                    id=int(id),
                    name=name,
                    columns=columns,
                    reference_table=fk['table'],
                    reference_columns=reference_columns,
                    on_update=fk.get('on_update', ''),
                    on_delete=fk.get('on_delete', ''),
                )
            )

        return results

    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[SQLiteRecord]:
        LOG_QUERY.append(f"/* get_records for table={table.name} */")
        if table is None :
            print("error")

        query = f"SELECT * FROM `{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)

        results = []
        for i, record in enumerate(self.cursor.fetchall(), start=offset):
            results.append(
                SQLiteRecord(id=i, table=table, values=dict(record))
            )
        logger.debug(f"get records for table={table.name} results={results}")
        return results

    def build_empty_table(self, database: SQLDatabase):
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

    def build_empty_column(self, name: str, table: SQLTable, datatype: SQLDataType, **default_values) -> SQLiteColumn:
        return SQLiteColumn(
            id=SQLiteContext.get_temporary_id(table.columns),
            pos=-1,
            name="",
            table=table,
            datatype=datatype,
            **default_values
        )

    def build_empty_index(self, name: str, table: SQLiteTable, type: SQLiteIndexType, columns: List[str]) -> SQLiteIndex:
        return SQLiteIndex(
            id=SQLiteContext.get_temporary_id(table.indexes),
            pos=-1,
            name=name,
            type=type,
            columns=columns,
            table=table,
        )

    def build_empty_record(self, table: SQLiteTable, values: Dict[str, Any]) -> SQLiteRecord:
        return SQLiteRecord(
            id=SQLiteContext.get_temporary_id(table.records),
            table=table,
            values=values
        )
