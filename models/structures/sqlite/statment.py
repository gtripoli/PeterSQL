import re
import sqlite3

from typing import Dict, Optional, List

from helpers.logger import logger

from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.sqlite.indextype import SQLiteIndexType
from models.structures.statement import AbstractStatement, Transaction, LOG_QUERY


class SQLiteStatement(AbstractStatement):

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
                )
            )

        return results

    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        if table.id == -1:
            return []
        logger.debug("get columns")
        LOG_QUERY.append(f"/* get_columns */")

        self.execute(f"SELECT * FROM `{table.database.name}`.pragma_table_info('{table.name}')")
        columns_result = self.cursor.fetchall()

        results = []
        for col in columns_result:
            type_str = col['type']
            parsed_type = SQLiteStatement.parse_type(type_str)

            results.append(
                SQLColumn(
                    id=col['cid'] + 1,
                    name=col['name'],
                    datatype=SQLiteDataType.get_by_name(parsed_type.name),
                    is_nullable=not col['notnull'],
                    table=table,

                    server_default=col['dflt_value'],
                    is_auto_increment=False,

                    length=parsed_type.length,

                    numeric_precision=parsed_type.precision,
                    numeric_scale=parsed_type.scale,
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
                     f"`id`, `table`, GROUP_CONCAT(`from`) as `from`, GROUP_CONCAT(`to`) as `to`, `on_update`, `on_delete`"
                     f"FROM `{table.database.name}`.pragma_foreign_key_list('{table.name}') GROUP BY id;")
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

    def get_records(self, database: SQLDatabase, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[Dict]:
        LOG_QUERY.append("/* get_records */")
        query = f"SELECT * FROM `{database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)
        results = self.cursor.fetchall()

        return [dict(row) for row in results]

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

    def rename_table(self, table: SQLTable, name: str) -> bool:
        sql = f"ALTER TABLE `{table.name}` RENAME TO `{name}`;"
        self.execute(sql)
        return True

    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        column_definition = [SQLiteStatement.build_column_definition(table, c) for c in table.columns]

        pk = next((idx for idx in table.indexes if idx.type == SQLiteIndexType.PRIMARY), None)
        constraints = []
        if pk and pk.columns:
            cols = ", ".join([f"`{c}`" for c in pk.columns])
            constraints.append(f"PRIMARY KEY ({cols})")

        for fk in table.foreign_keys:
            cols = ", ".join([f"`{c}`" for c in fk.columns])
            ref_cols = ", ".join([f"`{c}`" for c in fk.reference_columns])
            constraint = f"FOREIGN KEY ({cols}) REFERENCES {fk.reference_table} ({ref_cols})"
            if fk.on_update and fk.on_update != "NO ACTION":
                constraint += f" ON UPDATE {fk.on_update}"
            if fk.on_delete and fk.on_delete != "NO ACTION":
                constraint += f" ON DELETE {fk.on_delete}"
            constraints.append(constraint)

        sql = f"CREATE TABLE `{table.name}` ({', '.join(column_definition + constraints)})"

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
                                columns.append(col.name)
                            else:
                                columns.append(f"{original_column_map[col_id].name} as {col.name}")
                        else:
                            columns.append(f"'' as {col.name}")

                    self.rename_table(table, temp_name)

                    # Create table with primary keys and foreign keys
                    self.create_table(database, table)

                    self.execute(f"INSERT INTO `{table.name}` SELECT {', '.join(columns)}  FROM `{temp_name}`;")

                    self.execute(f"DROP TABLE {temp_name};")

                    for index in table_indexes:
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

        except:
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
