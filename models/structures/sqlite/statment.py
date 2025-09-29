import re
import uuid
import sqlite3

from typing import Iterator, Dict, Optional

from helpers.logger import logger

from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.sqlite.indextype import SQLiteIndexType
from models.structures.statement import AbstractStatement, Transaction, LOG_QUERY


class SQLiteStatement(AbstractStatement):

    def __init__(self, session):
        self.filename = session.configuration.filename

        self.connection_url = f"sqlite:///{self.filename}"

        super().__init__(self.connection_url)

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

    def get_databases(self) -> Iterator[SQLDatabase]:
        yield SQLDatabase(id=0, name='main', get_tables_handler=self.get_tables)

    def get_tables(self, database: SQLDatabase) -> Iterator[SQLTable]:
        self.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_result = self.cursor.fetchall()

        for i, row in enumerate(tables_result):
            yield SQLTable(
                id=i,
                name=row['name'],
                database=database,
                engine='sqlite',
                get_columns_handler=self.get_columns,
                get_indexes_handler=self.get_indexes,
            )

    def get_columns(self, table: SQLTable) -> Iterator[SQLColumn]:
        if table.id == -1:
            return

        self.execute(f"PRAGMA table_info({table.name})")
        columns_result = self.cursor.fetchall()

        for col in columns_result:
            type_str = col['type']
            parsed_type = self._parse_type(type_str)

            yield SQLColumn(
                id=col['cid'] + 1,
                name=col['name'],
                datatype=SQLiteDataType.get_by_name(parsed_type.name),
                is_nullable=not col['notnull'],
                table=table,
                is_primary_key=bool(col['pk']),

                # key='PRI' if col['pk'] else None,

                server_default=col['dflt_value'],
                is_auto_increment=False,

                length=parsed_type.length,

                numeric_precision=parsed_type.precision,
                numeric_scale=parsed_type.scale,

                # indexes=[idx for idx in indexes if column.name in idx.columns],
                # get_indexes_handler=self.get_indexes
            )

    def get_indexes(self, table: SQLTable) -> Iterator[SQLIndex]:
        if table.id == -1:
            return

        self.execute(f"PRAGMA table_info({table.name})")
        table_info = self.cursor.fetchall()
        pk_columns = sorted([row['name'] for row in table_info if row['pk'] > 0])

        self.execute(f"PRAGMA index_list({table.name})")
        indexes = self.cursor.fetchall()

        for idx in indexes:
            name = idx['name']
            is_unique = bool(idx['unique'])
            is_partial = bool(idx['partial'])
            origin = idx['origin']
            is_expression = False

            self.execute(f"PRAGMA index_info({name})")
            index_info = self.cursor.fetchall()

            self.execute(f"SELECT sql FROM sqlite_master WHERE tbl_name = '{table.name}' AND name = '{name}';")
            sql_row = self.cursor.fetchone()
            sql = sql_row['sql'] if sql_row else None

            columns = []
            expression = None
            partial_condition = None

            for row in index_info:
                if row['cid'] == -2:
                    is_expression = True
                else:
                    columns.append(row['name'])

            if sql:
                # Parse the SQL to extract expression and partial condition
                match = re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+\w+\s*\(([^)]+\))\)(?:\s+WHERE\s+(.+))?', sql, re.IGNORECASE | re.DOTALL)
                if match:
                    expr_part = match.group(1).strip()
                    where_part = match.group(2).strip() if match.group(2) else None
                    if is_expression:
                        expression = expr_part
                        partial_condition = where_part
                    else:
                        partial_condition = where_part

            # Determine index type
            if set(columns) == set(pk_columns) and is_unique and origin == 'u':
                index_type = SQLiteIndexType.PRIMARY
            elif is_partial:
                index_type = SQLiteIndexType.PARTIAL
            elif is_expression:
                index_type = SQLiteIndexType.EXPRESSION
            elif is_unique:
                index_type = SQLiteIndexType.UNIQUE
            elif len(columns) > 1:
                index_type = SQLiteIndexType.COVERING
            else:
                index_type = SQLiteIndexType.INDEX

            yield SQLIndex(
                name=name,
                type=index_type,
                columns=columns,
                expression=expression,
                partial_condition=partial_condition,
            )

    def _build_create_index_sql(self, table: SQLTable, index: SQLIndex) -> str:
        if index.type == SQLiteIndexType.PRIMARY:
            return ""  # PRIMARY is handled in table creation

        unique_str = "UNIQUE " if index.type == SQLiteIndexType.UNIQUE else ""

        if index.type == SQLiteIndexType.EXPRESSION:
            expr = index.expression
        else:
            expr = ", ".join(index.columns)

        where_str = f"WHERE {index.partial_condition}" if index.partial_condition else ""

        sql = f"CREATE {unique_str}INDEX {index.name} ON {table.name}({expr}) {where_str}"
        return sql

    def _create_index(self, table: SQLTable, index: SQLIndex):
        sql = self._build_create_index_sql(table, index)
        if sql:
            self.execute(sql)

    def _drop_index(self, table: SQLTable, index: SQLIndex):
        if index.type in [SQLiteIndexType.PRIMARY, SQLiteIndexType.UNIQUE] :
            old_table_name = self._rename_table(table)

            create_sql = self._build_create_table_sql(table)
            self.execute(create_sql)

            # Copy data (use current model columns, they should be compatible)
            cols = ", ".join([f"`{c.name}`" for c in table.columns])
            insert_sql = f"INSERT INTO `{table.name}` ({cols}) SELECT {cols} FROM {old_table_name};"
            self.execute(insert_sql)

            # Drop old table
            self.execute(f"DROP TABLE {old_table_name};")

            # Recreate non-primary indexes as per model (the dropped constraint won't be recreated if removed from model)
            for idx in table.indexes:
                if idx.name != index.name:
                    self._create_index(table, idx)

            return

        # Normal droppable index
        sql = f"DROP INDEX IF EXISTS {index.name}"
        self.execute(sql)

    def build_new_table(self, database: SQLDatabase):
        return SQLTable(
            id=-1,
            name='',
            database=database,
            engine='sqlite',
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
        )

    def _rename_table(self, table: SQLTable) -> str:
        id = str(uuid.uuid4())[::-1][:8]
        name = f"`_{table.name}_{id}`"

        sql = f"ALTER TABLE `{table.name}` RENAME TO {name};"
        self.execute(sql)

        return name

    def _add_column(self, table: SQLTable, column: SQLColumn):
        sql = f"ALTER TABLE `{table.name}` ADD COLUMN {self.build_column_definition(table, column)}"
        self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn):

        old_table_name = self._rename_table(table)

        existing_columns = table.columns

        for i, c in enumerate(existing_columns):
            if c.name == column.name:
                existing_columns[i] = column
                break

        column_defs = [self.build_column_definition(table, c) for c in existing_columns]
        sql = f"CREATE TABLE `{table.name}` ({', '.join(column_defs)})"
        self.execute(sql)

        sql = f"INSERT INTO `{table.name}` SELECT * FROM {old_table_name};"
        self.execute(sql)

        sql = f"DROP TABLE {old_table_name};"
        self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn):
        old_table_name = self._rename_table(table)

        existing_columns = table.columns

        for i, c in enumerate(existing_columns):
            if c.name == column.name:
                del existing_columns[i]
                break

        column_defs = [self.build_column_definition(table, c) for c in existing_columns]
        sql = f"CREATE TABLE `{table.name}` ({', '.join(column_defs)})"
        self.execute(sql)

        sql = f"INSERT INTO `{table.name}` SELECT {', '.join([c.name for c in existing_columns])} FROM {old_table_name};"
        self.execute(sql)

        sql = f"DROP TABLE {old_table_name};"
        self.execute(sql)

    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        try:
            self.execute(self._build_create_table_sql(table))
            for index in table.indexes:
                if index.type != SQLiteIndexType.PRIMARY:
                    self._create_index(table, index)
            return True
        except Exception as e:
            logger.error(f"Error creating table {table.name}: {e}")
            return False

    def update_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        existing_columns = list(self.get_columns(table))

        existing_columns_map = {col.name: col for col in existing_columns}

        new_columns_map = {col.name: col for col in table.columns}

        columns_to_add = []
        columns_to_modify = []

        for col_name, new_col in new_columns_map.items():
            if col_name not in existing_columns_map:
                columns_to_add.append(new_col)
            else:
                existing_col = existing_columns_map[col_name]
                if existing_col != new_col:
                    columns_to_modify.append(new_col)

        columns_to_drop = [col for col_name, col in existing_columns_map.items() if col_name not in new_columns_map]

        existing_indexes = list(self.get_indexes(table))
        existing_indexes_map = {idx.name: idx for idx in existing_indexes}

        new_indexes_map = {idx.name: idx for idx in table.indexes}

        indexes_to_add = []
        indexes_to_modify = []

        for idx_name, new_idx in new_indexes_map.items():
            if idx_name not in existing_indexes_map:
                indexes_to_add.append(new_idx)
            else:
                existing_idx = existing_indexes_map[idx_name]
                if existing_idx != new_idx:
                    indexes_to_modify.append(new_idx)

        indexes_to_drop = [idx for idx_name, idx in existing_indexes_map.items() if idx_name not in new_indexes_map]

        try:
            with Transaction(self):
                for col in columns_to_add:
                    self._add_column(table, col)

                for col in columns_to_modify:
                    self._modify_column(table, col)

                for col in columns_to_drop:
                    self._drop_column(table, col)

                for idx in indexes_to_drop:
                    self._drop_index(table, idx)

                for idx in indexes_to_add:
                    self._create_index(table, idx)

                for idx in indexes_to_modify:
                    self._drop_index(table, idx)
                    self._create_index(table, idx)
        except Exception as ex:
            log = f"Error altering table name={table.name}: {str(ex)}"
            logger.error(log)
            LOG_QUERY.append(log)
            return False

        return True

    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        sql = f"DROP TABLE `{database.name}`.`{table.name}`"
        return self._execute_transaction(sql, f"drop table {table.name}")

    def _build_create_table_sql(self, table: SQLTable) -> str:
        column_defs = [self.build_column_definition(table, c) for c in table.columns]

        pk = next((idx for idx in table.indexes if idx.type == SQLiteIndexType.PRIMARY), None)
        constraints = []
        if pk and pk.columns:
            cols = ", ".join([f"`{c}`" for c in pk.columns])
            constraints.append(f"PRIMARY KEY ({cols})")

        parts = column_defs + constraints
        return f"CREATE TABLE `{table.name}` ({', '.join(parts)})"

    def get_records(self, database: SQLDatabase, table: SQLTable, limit: int = 1000, offset: int = 0) -> Iterator[Dict]:
        query = f"SELECT * FROM `{database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)
        results = self.cursor.fetchall()

        for row in results:
            yield dict(row)
