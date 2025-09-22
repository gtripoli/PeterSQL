import uuid
import sqlite3
from typing import Iterator, Dict, Optional

from helpers.logger import logger

from models.structures.database import SQLDatabase, SQLTable, SQLColumn
from models.structures.sqlite.datatype import SQLiteDataType
from models.structures.statement import AbstractStatement, Transaction, LOG_QUERY


class SQLiteStatement(AbstractStatement):

    def __init__(self, session):
        self.filename = session.configuration.filename

        self.connection_url = f"sqlite:///{self.filename}"

        super().__init__(self.connection_url)

    def _get_column_definition(self, table: SQLTable, column: SQLColumn):
        parts = [f"`{column.name}`"]

        datatype_parts = str(column.datatype.name)

        if column.datatype.has_length:
            datatype_parts += f"({column.length or column.datatype.default_length})"

        if column.datatype.has_precision:
            if column.datatype.has_scale:
                datatype_parts += f"({column.numeric_precision or column.datatype.default_precision},{column.numeric_scale or column.datatype.default_scale})"
            else:
                datatype_parts += f"({column.numeric_precision or column.datatype.default_precision})"

        if column.datatype.has_set:
            datatype_parts += f"""('{"','".join(list(set(column.set or column.datatype.default_set)))}')"""

        parts.append(datatype_parts)

        if not column.is_nullable:
            parts.append("NOT NULL")
        else:
            parts.append("NULL")

        if column.default and column.default != '':
            parts.append(f"DEFAULT {column.default}")

        return " ".join(parts)

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
            )

    def get_columns(self, database: SQLDatabase, table: SQLTable) -> Iterator[SQLColumn]:
        if table.id is None:
            return

        self.execute(f"PRAGMA table_info({table.name})")
        columns_result = self.cursor.fetchall()

        for col in columns_result:
            type_str = col['type']
            parsed_type = self._parse_type(type_str)

            yield SQLColumn(
                id=col['cid'],
                name=col['name'],
                datatype=SQLiteDataType.get_by_name(parsed_type.name),
                is_nullable=not col['notnull'],
                extra=None,
                key='PRI' if col['pk'] else None,
                comment=None,
                server_default=col['dflt_value'],
                is_unsigned=False,
                is_zerofill=False,
                is_auto_increment=False,
                set=None,
                length=parsed_type.length,
                collation_name=None,
                numeric_precision=parsed_type.precision,
                numeric_scale=parsed_type.scale,
                datetime_precision=None,
                virtuality=None,
                expression=None,
                indexes=[]
            )

    def get_records(self, database : SQLDatabase, table: SQLTable, limit: int = 1000, offset: int = 0) -> Iterator[Dict]:
        query = f"SELECT * FROM `{database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)
        results = self.cursor.fetchall()

        for row in results:
            yield dict(row)

    def build_new_table(self, database: SQLDatabase):
        return SQLTable(
            id=-1,
            name='',
            database=database,
            engine='sqlite',
            get_columns_handler=self.get_columns,
        )

    def _add_column(self, table: SQLTable, column: SQLColumn):
        sql = f"ALTER TABLE `{table.name}` ADD COLUMN {self._get_column_definition(table, column)}"
        self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn):
        id = str(uuid.uuid4())[::-1][:8]
        old_name = f"`_old_{table.name}_{id}`"

        sql = f"ALTER TABLE `{table.name}` RENAME TO {old_name};"
        self.execute(sql)

        existing_columns = table.columns

        for i, c in enumerate(existing_columns):
            if c.name == column.name:
                existing_columns[i] = column
                break

        column_defs = [self._get_column_definition(table, c) for c in existing_columns]
        sql = f"CREATE TABLE `{table.name}` ({', '.join(column_defs)})"
        self.execute(sql)

        sql = f"INSERT INTO `{table.name}` SELECT * FROM {old_name};"
        self.execute(sql)

        sql = f"DROP TABLE {old_name};"
        self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn):
        # SQLite non supporta DROP COLUMN
        logger.warning(f"SQLite does not support DROP COLUMN for {column.name}")

    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        column_defs = [self._get_column_definition(table, c) for c in table.columns]
        sql = f"CREATE TABLE `{table.name}` ({', '.join(column_defs)})"

        return self._execute_transaction(sql, f"create table {table.name}")

    def update_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        existing_columns = list(self.get_columns(database, table))

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

        try:
            with Transaction(self):
                for col in columns_to_add:
                    self._add_column(table, col)

                for col in columns_to_modify:
                    self._modify_column(table, col)

                for col in columns_to_drop:
                    self._drop_column(table, col)
        except Exception as ex:
            log = f"Error altering table name={table.name}: {str(ex)}"
            logger.error(log)
            LOG_QUERY.append(log)
            return False

        return True

    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        sql = f"DROP TABLE `{database.name}`.`{table.name}`"
        return self._execute_transaction(sql, f"drop table {table.name}")
