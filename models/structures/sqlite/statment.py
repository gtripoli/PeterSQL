import re
import sqlite3
from typing import Dict, Optional, List, Any, NamedTuple

from helpers.logger import logger

from models.structures.statement import LOG_QUERY, AbstractColumnBuilder, AbstractStatement, Transaction
from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord

from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.sqlite.indextype import SQLiteIndexType

#     column_name data_type
#         [PRIMARY KEY [ASC|DESC] [AUTOINCREMENT]]
#         [NOT NULL]
#         [UNIQUE]
#         [CHECK (expression)]
#         [DEFAULT default_value]
#         [COLLATE collation_name]
#         [REFERENCES foreign_table(column_name)
#             [ON DELETE {SET NULL | SET DEFAULT | CASCADE | RESTRICT | NO ACTION}]
#             [ON UPDATE {SET NULL | SET DEFAULT | CASCADE | RESTRICT | NO ACTION}]
#         ]
#         [GENERATED ALWAYS AS (expression) [VIRTUAL | STORED]]
# https://sqlite.org/syntax/column-constraint.html

COLUMN_PATTERN = re.compile(r"""
^\s*
(?:`|\"|\[)?(?P<name>\w+)(?:`|\"|\])?                                                       # column name
\s+
(?P<datatype>\w+)                                                                           # data type (ex. VARCHAR, INT)
(?:\s*\((?P<length>\d+)|(?P<precision>\d+),(?P<scale>\d+)|(?P<set>.*)\))?                   # length or precision and scale or set
(?:\s+(?P<primary>PRIMARY\s+KEY)(?:\s+(ASC|DESC)?)?)?                                       # PK inline
(?:\s+(?P<conflict_clause_pk>ON\s+CONFLICT\s+(ROLLBACK|ABORT|FAIL|IGNORE|REPLACE)))?        # conflict clause primary key
(?:\s+(?P<auto>AUTOINCREMENT))?                                                             # auto increment
(?:\s+(?P<null>NOT\s+NULL|NULL))?                                                           # nullability
(?:\s+(?P<conflict_clause_null>ON\s+CONFLICT\s+(ROLLBACK|ABORT|FAIL|IGNORE|REPLACE)))?      # conflict clause nullability
(?:\s+(?P<unique>UNIQUE))?                                                                  # UNIQUE inline
(?:\s+(?P<conflict_clause_unique>ON\s+CONFLICT\s+(ROLLBACK|ABORT|FAIL|IGNORE|REPLACE)))?    # conflict clause unique
(?:\s+(?P<check>CHECK\s*\(.*?\)))?                                                          # CHECK constraint
(?:\s+(?P<conflict_clause_check>ON\s+CONFLICT\s+(ROLLBACK|ABORT|FAIL|IGNORE|REPLACE)))?     # conflict clause check
(?:\s+(?P<default>DEFAULT\s+(?:NULL|CURRENT_TIMESTAMP|'.*?'|".*?"|[^\s,]+)))?               # default value
(?:\s+(?P<collate>COLLATE\s+\w+))?                                                          # COLLATE
(?:\s+(?P<generated>GENERATED\s+ALWAYS\s+AS\s*\(.*?\)\s*(?:VIRTUAL|STORED)?))?              # colonne generate
\s*(?=,|\)|$)                                                                               # lookahead: end before , ) or end of string
""", re.IGNORECASE | re.VERBOSE)


class SQLiteColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(primary_key)s", "%(auto_increment)s", "%(nullable)s", "%(check)s", "%(default)s", "%(collate)s", "%(generated)s"]

    def __init__(self, column: SQLColumn):
        super().__init__(column)

        self.parts.update({
            'generated': self.generated,
        })

    @property
    def primary_key(self):
        return 'PRIMARY KEY' if self.column.is_primary_key or self.column.is_auto_increment else ''

    @property
    def auto_increment(self):
        return 'AUTOINCREMENT' if self.column.is_auto_increment else ''

    @property
    def generated(self):
        return f"GENERATED ALWAYS AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality is not None else ''


class SQLiteStatement(AbstractStatement):
    _column_builder = SQLiteColumnBuilder

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
        # self.execute("PRAGMA temp_store = MEMORY")
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
        return [SQLDatabase(id=0, name='main', get_tables_handler=self.get_tables)]

    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        self.execute("SELECT * FROM sqlite_master WHERE type IN('table', 'view', 'trigger') AND name NOT LIKE 'sqlite_%' ORDER BY name")

        results = []
        for row in self.cursor.fetchall():
            results.append(
                SQLTable(
                    id=row['rootpage'],
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

    def parse_create_table(self, sql_create_table: str) -> List[Dict[str, Any]]:
        results = []

        return results

    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        results = []
        if table.id == -1:
            return results

        LOG_QUERY.append(f"/* get_columns */")

        self.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table.name}'")
        if not (sql_table_result := self.cursor.fetchone()):
            return results

        sql_create_table = sql_table_result['sql']

        if not (table_match := re.search(r'CREATE\s+TABLE\s+(?:`?\w+`?\s+)?\((?P<columns>.*)\)', sql_create_table, re.IGNORECASE | re.DOTALL).groupdict()):
            return results

        columns = [c.strip() for c in table_match['columns'].split(", ")]
        for i, column in enumerate(columns):
            if not (columns_match := COLUMN_PATTERN.match(column)):
                continue

            if column.startswith("PRIMARY KEY") or column.startswith("UNIQUE") or column.startswith("FOREIGN KEY"):
                continue

            column_dict = columns_match.groupdict()

            results.append(
                SQLColumn(
                    id=i,
                    name=column_dict["name"],
                    datatype=SQLiteDataType.get_by_name(column_dict['datatype']),
                    is_nullable=column_dict.get('null', "NULL") == "NULL",
                    table=table,
                    server_default=column_dict['default'],
                    is_auto_increment=column_dict["auto"] == "AUTOINCREMENT",
                    length=column_dict['length'],
                    numeric_precision=column_dict['precision'],
                    numeric_scale=column_dict['scale'],
                    set=column_dict['set'],
                )
            )

        return results

    def get_indexes(self, table: SQLTable) -> List[SQLIndex]:
        if table.id == -1:
            return []
        logger.debug("get_indexes")

        LOG_QUERY.append("/* get_indexes */")

        results = []

        self.execute(f"SELECT * FROM `{table.database.name}`.pragma_table_info('{table.name}') WHERE pk != 0 ORDER BY pk;")
        pk_index = self.cursor.fetchall()
        if len(pk_index):
            results.append(
                SQLIndex(
                    id=0,
                    name="PRIMARY KEY",
                    type=SQLiteIndexType.PRIMARY,
                    columns=[col['name'] for col in pk_index],
                )
            )

        self.execute(f"SELECT * FROM `test`.pragma_index_list('{table.name}') WHERE `origin` != 'pk' order by seq desc;")
        indexes = [dict(row) for row in self.cursor.fetchall()]

        for idx in indexes:
            id = int(idx['seq']) + 1
            name = idx['name']
            is_unique = bool(idx.get('unique', False))
            is_partial = bool(idx.get('partial', False))
            # is_primary = bool(idx.get('primary', idx.get('origin') == 'pk'))
            # origin = idx.get('origin', '')
            is_expression = False

            self.execute(f"SELECT * FROM '{table.name}'.pragma_index_info('{name}');")
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
                SQLIndex(
                    id=id,
                    name=name,
                    type=index_type,
                    columns=columns,
                    condition=condition,
                    expression=expression,
                )
            )

        type_order = {t: i for i, t in enumerate(SQLiteIndexType.get_all())}
        results.sort(key=lambda idx: type_order.get(idx.type, 999))

        return results

    def get_foreign_keys(self, table: SQLTable) -> List[SQLForeignKey]:
        if table.id == -1:
            return []
        logger.debug("get_foreign_keys")

        LOG_QUERY.append("/* get_foreign_keys */")

        self.execute(f"SELECT"
                     f" `id`, `table`, GROUP_CONCAT(`from`) as `from`, GROUP_CONCAT(`to`) as `to`, `on_update`, `on_delete`"
                     f" FROM `{table.database.name}`.pragma_foreign_key_list('{table.name}') GROUP BY id;")
        foreign_keys = [dict(row) for row in self.cursor.fetchall()]

        results = []
        for fk in foreign_keys:
            id = fk['id']
            name = f"fk_{table.name}_{fk['table']}_{id}"

            columns = fk['from'].split(",")
            reference_columns = fk['to'].split(",")

            results.append(
                SQLForeignKey(
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

    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[SQLRecord]:
        LOG_QUERY.append("/* get_records */")
        query = f"SELECT * FROM `{table.database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)

        results = []
        for i, record in enumerate(self.cursor.fetchall(), start=offset):
            results.append(
                SQLRecord(_id=i, table=table, **dict(record))
            )
        return results

    def build_empty_table(self, database: SQLDatabase):
        return SQLTable(
            id=-1,
            name='',
            database=database,
            engine='sqlite',
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_foreign_keys_handler=self.get_foreign_keys,
        )

    # TABLES
    def rename_table(self, table: SQLTable, name: str) -> bool:
        sql = f"ALTER TABLE `{table.name}` RENAME TO `{name}`;"
        self.execute(sql)
        return True

    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        constraints = []
        columns_definitions = [str(self._column_builder(c)) for c in table.columns]

        primary_key_is_already_present = any(['PRIMARY KEY' in column_definition for column_definition in columns_definitions])
        foreign_key_is_already_present = any(['FOREIGN KEY' in column_definition for column_definition in columns_definitions])

        if not primary_key_is_already_present:
            pk = next((idx for idx in table.indexes if idx.type == SQLiteIndexType.PRIMARY), None)
            if pk and pk.columns:
                cols = ", ".join([f"`{c}`" for c in pk.columns])
                constraints.append(f"PRIMARY KEY ({cols})")

        if not foreign_key_is_already_present:
            for fk in table.foreign_keys:
                cols = ", ".join([f"`{c}`" for c in fk.columns])
                ref_cols = ", ".join([f"`{c}`" for c in fk.reference_columns])
                constraint = f"FOREIGN KEY ({cols}) REFERENCES {fk.reference_table} ({ref_cols})"
                if fk.on_update and fk.on_update != "NO ACTION":
                    constraint += f" ON UPDATE {fk.on_update}"
                if fk.on_delete and fk.on_delete != "NO ACTION":
                    constraint += f" ON DELETE {fk.on_delete}"
                constraints.append(constraint)

        sql = f"CREATE TABLE `{table.name}` ({', '.join(columns_definitions + constraints)})"

        return self.execute(sql)

    def alter_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        original_table = next((t for t in database.tables if t.id == table.id), None)
        original_columns = list(original_table.columns)
        original_indexes = list(original_table.indexes)
        original_primary_keys = next((pk for pk in original_indexes if pk.type == SQLiteIndexType.PRIMARY), None)
        original_foreign_keys = list(original_table.foreign_keys)

        table_columns = list(table.columns)
        table_indexes = list(table.indexes)
        table_primary_keys = next((pk for pk in table_indexes if pk.type == SQLiteIndexType.PRIMARY), None)
        table_foreign_keys = list(table.foreign_keys)

        original_column_map = {col.id: col for col in original_columns}
        table_column_map = {col.id: col for col in table_columns}
        original_index_map = {idx.id: idx for idx in original_indexes}
        table_index_map = {idx.id: idx for idx in table_indexes}

        needs_recreate = False

        # Check for columns changes
        if any([
            original_columns != table_columns,
            original_primary_keys != table_primary_keys,
            original_foreign_keys != table_foreign_keys
        ]):
            needs_recreate = True

        try:
            with Transaction(self):
                if current_table := next((t for t in database.tables if t.id == table.id), None):
                    if table.name != current_table.name:
                        self.rename_table(current_table, table.name)

                # SQLite does not support ALTER COLUMN or ADD CONSTRAINT,
                # so rename and recreate the table with the new columns and constraints
                if needs_recreate:
                    temp_name = f"_{table.name}_{self.generate_uuid()}"

                    columns = []

                    for col_id, col in table_column_map.items():
                        if col_id in original_column_map.keys():
                            if col.name == original_column_map[col_id].name:
                                columns.append(f"{col.name}")
                            else:
                                columns.append(f"{original_column_map[col_id].name} as `{col.name}`")
                        else:
                            columns.append(f"'' as `{col.name}`")

                    self.rename_table(table, temp_name)

                    # Create table with primary keys and foreign keys
                    self.create_table(database, table)

                    self.execute(f"INSERT INTO `{table.name}` SELECT {', '.join(columns)}  FROM `{temp_name}`;")

                    self.execute(f"DROP TABLE {temp_name};")

                    for index in [i for i in table_indexes if i.type != SQLiteIndexType.PRIMARY]:
                        self._create_index(table, index)

                else:
                    # Perform supported ALTER operations
                    for col_id, col in table_column_map.items():
                        if col_id not in original_column_map.keys():
                            self._add_column(table, col)

                        elif col_id in original_column_map.keys() and col.name != original_column_map[col_id].name:
                            self._rename_column(table, original_column_map[col_id], col.name)

                    for col_id, original_col in original_column_map.items():
                        if col_id not in table_column_map.keys():
                            self._drop_column(table, original_col)

                    # Handle indexes
                    for idx_id, idx in table_index_map.items():
                        if idx_id not in original_index_map:
                            self._create_index(table, idx)
                        else:
                            if idx != original_index_map[idx_id]:
                                self._drop_index(table, original_index_map[idx_id])
                                self._create_index(table, idx)

                    for idx_id, idx in original_index_map.items():
                        if idx_id not in table_index_map:
                            self._drop_index(table, idx)

        except Exception as ex:
            LOG_QUERY.append(f"/* alter_table */ {ex}")
            logger.error(ex, exc_info=True)

            return False

        return True

    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        sql = f"DROP TABLE `{database.name}`.`{table.name}`"
        return self.execute(sql)

    # COLUMNS
    def _add_column(self, table: SQLTable, column: SQLColumn) -> bool:
        sql = f"ALTER TABLE `{table.name}` ADD COLUMN {SQLiteStatement.build_column_definition(table, column)}"
        return self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn):
        new_name = f"_{table.name}_{self.generate_uuid()}"

        self.rename_table(table, new_name)

        for i, c in enumerate(table.columns):
            if c.name == column.name:
                table.columns[i] = column
                break

        self.create_table(table.database, table)

        sql = f"INSERT INTO `{table.name}` SELECT * FROM {new_name};"
        self.execute(sql)

        sql = f"DROP TABLE {new_name};"
        self.execute(sql)

    def _rename_column(self, table: SQLTable, column: SQLColumn, new_name: str) -> bool:
        return self.execute(f"ALTER TABLE `{table.name}` RENAME COLUMN `{column.name}` TO `{new_name}`")

    def _drop_column(self, table: SQLTable, column: SQLColumn) -> bool:
        return self.execute(f"ALTER TABLE `{table.name}` DROP COLUMN `{column.name}`")

    def _recreate_table_for_foreign_keys(self, table: SQLTable):
        new_name = f"_{table.name}_{self.generate_uuid()}"

        self.rename_table(table, new_name)

        self.create_table(table.database, table)

        cols = ", ".join([f"`{c.name}`" for c in table.columns])
        insert_sql = f"INSERT INTO `{table.name}` ({cols}) SELECT {cols} FROM {new_name};"
        self.execute(insert_sql)

        # Drop old table
        self.execute(f"DROP TABLE {new_name};")

        # Recreate non-primary indexes
        for idx in table.indexes:
            if idx.type != SQLiteIndexType.PRIMARY:
                self._create_index(table, idx)

    # INDEXES
    def _create_index(self, table: SQLTable, index: SQLIndex) -> bool:
        if index.type == SQLiteIndexType.PRIMARY:
            return False  # PRIMARY is handled in table creation

        unique_index = "UNIQUE INDEX" if index.type == SQLiteIndexType.UNIQUE else "INDEX"

        if index.type == SQLiteIndexType.EXPRESSION:
            expression = ", ".join(index.expression)
        else:
            expression = ", ".join(index.columns)

        where_str = f"WHERE {index.condition}" if index.condition else ""

        return self.execute(f"CREATE {unique_index} IF NOT EXISTS {index.name} ON {table.name}({expression}) {where_str}")

    def _drop_index(self, table: SQLTable, index: SQLIndex) -> bool:
        sql = f"DROP INDEX IF EXISTS {index.name}"
        return self.execute(sql)

    # RECORDS
    def insert_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> bool:
        with Transaction(self):
            if raw_insert_record := self.raw_insert_record(database, table, record):
                return self.execute(raw_insert_record)

            return False

    def update_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> bool:
        with Transaction(self):
            if raw_update_record := self.raw_update_record(database, table, record):
                return self.execute(raw_update_record)

            return False

    def delete_records(self, database: SQLDatabase, table: SQLTable, records: List[SQLRecord]) -> bool:
        results = []
        with Transaction(self):
            for record in records:
                if raw_delete_record := self.raw_delete_record(database, table, record):
                    results.append(self.execute(raw_delete_record))

        return all(results)
