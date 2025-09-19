import re
from typing import Iterator, List, Optional, Union, Dict

import pymysql

from helpers.logger import logger
from models.structures.charset import COLLATION_CHARSETS
from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex
from models.structures.statement import AbstractStatement, LOG_QUERY
from models.structures.mariadb.datatype import MariaDBDataType


class MariaDBStatement(AbstractStatement):

    def __init__(self, session):
        # Parse connection details from session
        self.host = session.configuration.hostname
        self.user = session.configuration.username
        self.password = session.configuration.password
        self.database = getattr(session.configuration, 'database', None)

        # Create connection URL for compatibility
        self.connection_url = f"mysql://{self.user}:{self.password}@{self.host}"
        if self.database:
            self.connection_url += f"/{self.database}"

        super().__init__(self.connection_url)

    @staticmethod
    def _parse_type(column_type: str) -> Optional[Union[int, List[str]]]:
        int_match = re.search(r'\((\d+)\)', column_type)
        if int_match:
            return int(int_match.group(1))

        enum_match = re.search(r'^(enum|set)\((.*)\)$', column_type)
        if enum_match:
            inner = enum_match.group(2)
            return [value.strip("'") for value in inner.split(",")]

        return None

    @staticmethod
    def _get_column_definition(table: SQLTable, column: SQLColumn):
        # ALTER TABLE tbl_name
        # MODIFY [COLUMN] col_name
        #     data_type[(length)][UNSIGNED|SIGNED|ZEROFILL]
        #     [CHARACTER SET charset_name] [COLLATE collation_name]
        #     [GENERATED ALWAYS] [AS (expr)] [VIRTUAL | STORED]
        #     [NOT NULL | NULL]
        #     [DEFAULT default_value]
        #     [AUTO_INCREMENT]
        #     [UNIQUE [KEY] | PRIMARY KEY]
        #     [COMMENT 'string']
        #     [COLUMN_FORMAT {FIXED|DYNAMIC|DEFAULT}]
        #     [STORAGE {DISK|MEMORY|DEFAULT}]
        #     [reference_definition]

        parts = [f"`{column.name}`", str(column.datatype.name)]

        if column.datatype.has_length:
            parts.append(f"({column.length or column.datatype.default_length})")

        if column.datatype.has_precision:
            if column.datatype.has_scale:
                parts.append(f"({column.numeric_precision or column.datatype.default_precision}, {column.numeric_scale or column.datatype.default_scale})")
            else:
                parts.append(f"({column.numeric_precision or column.datatype.default_precision})")

        if column.datatype.has_set:
            parts.append(f"""('{"','".join(list(set(column.set or column.datatype.default_set)))}')""")

        if column.datatype.has_unsigned and column.is_unsigned:
            parts.append("UNSIGNED")

        if column.datatype.has_zerofill and column.is_zerofill:
            parts.append("ZEROFILL")

        if column.datatype not in [MariaDBDataType.JSON]:
            if column.collation_name and column.collation_name != table.collation_name:
                parts.append(f"CHARACTER SET {COLLATION_CHARSETS[column.collation_name]} COLLATE {column.collation_name}")

        if column.virtuality and column.expression:
            parts.append(f"AS ({column.expression}) {column.virtuality}")

        else:
            if not column.is_nullable:
                parts.append("NOT NULL")
            else:
                parts.append("NULL")

            if column.default == "AUTO_INCREMENT":
                parts.append("AUTO_INCREMENT")
            elif column.default != '':
                parts.append(f"DEFAULT {column.default}")

        print("EXTRA", column.extra)
        # if column.extra:
        #     parts.append(column.extra)

        if column.comment:
            parts.append(f"COMMENT '{column.comment}'")

        return " ".join(parts)

    def connect(self, **connect_kwargs) -> None:
        """Establish connection to MariaDB/MySQL database using pymysql"""
        if self._connection is None:
            try:
                self._connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    **connect_kwargs
                )
                self._cursor = self._connection.cursor()
                self._on_connect()
            except Exception as e:
                logger.error(f"Failed to connect to MariaDB: {e}")
                raise

    def get_server_version(self) -> str:
        self.execute("SELECT VERSION()")
        version = self.cursor.fetchone()
        return version['VERSION()']

    def get_server_uptime(self) -> int:
        self.execute("SHOW STATUS LIKE 'Uptime'")
        uptime = self.cursor.fetchone()

        uptime_value = int(uptime['Value'])

        return uptime_value

    def get_databases(self) -> Iterator[SQLDatabase]:
        self.execute("SHOW DATABASES")
        databases = self.cursor.fetchall()

        for index, row in enumerate(databases):
            database_name = row['Database']
            yield SQLDatabase(
                id=index,
                name=database_name,
                get_tables_handler=self.get_tables
            )

    def get_tables(self, database: SQLDatabase) -> Iterator[SQLTable]:
        self.execute(f"""
            SELECT TABLE_NAME, TABLE_ROWS, ENGINE, TABLE_COLLATION
            FROM `information_schema`.`tables`
            WHERE table_schema = '{database.name}'
                AND table_type = 'BASE TABLE'
        """)
        tables_result = self.cursor.fetchall()

        for i, row in enumerate(tables_result):
            yield SQLTable(
                id=i,
                name=row['TABLE_NAME'],
                database=database,
                engine=row['ENGINE'],
                collation_name=row['TABLE_COLLATION'],
                get_columns_handler=self.get_columns
            )

    def get_columns(self, database: SQLDatabase, table: SQLTable) -> Iterator[SQLColumn]:
        self.execute(f"""
            SELECT *
            FROM `information_schema`.`columns`
            WHERE table_schema = '{database.name}'
                AND table_name = '{table.name}'
            ORDER BY ORDINAL_POSITION
        """)
        columns_result = self.cursor.fetchall()

        self.execute(f"""
            SELECT *
            FROM `information_schema`.`statistics`
            WHERE table_schema = '{database.name}'
                AND table_name = '{table.name}'
        """)
        indexes_result = self.cursor.fetchall()

        indexes_map = {}
        for idx in indexes_result:
            col_name = idx['COLUMN_NAME']
            if col_name not in indexes_map:
                indexes_map[col_name] = []
            indexes_map[col_name].append(idx)

        for col in columns_result:
            column_indexes = []
            for idx in indexes_map.get(col['COLUMN_NAME'], []):
                index_type = idx['INDEX_TYPE']
                if idx['INDEX_NAME'] == 'PRIMARY':
                    index_type = 'PRIMARY'

                index_obj = SQLIndex(
                    name=idx['INDEX_NAME'],
                    type=index_type,
                    columns=[idx['COLUMN_NAME']],
                    is_primary=(idx['INDEX_NAME'] == 'PRIMARY'),
                    is_unique=(idx['NON_UNIQUE'] == 0),
                    is_fulltext=(index_type == 'FULLTEXT'),
                    is_spatial=(index_type == 'SPATIAL')
                )
                column_indexes.append(index_obj)

            yield SQLColumn(
                id=col['ORDINAL_POSITION'],
                name=col['COLUMN_NAME'],
                datatype=MariaDBDataType.get_by_name(col['DATA_TYPE'], col=col),
                is_nullable=col['IS_NULLABLE'] == 'YES',
                extra=col['EXTRA'] if col['EXTRA'] not in ['', 'auto_increment', 'VIRTUAL GENERATED', 'STORED GENERATED'] else None,
                key=col['COLUMN_KEY'],

                collation_name=col['COLLATION_NAME'] if col['COLLATION_NAME'] != table.collation_name else None,
                comment=col['COLUMN_COMMENT'],
                is_unsigned='unsigned' in col['COLUMN_TYPE'],
                is_zerofill='zerofill' in col['COLUMN_TYPE'],

                virtuality="VIRTUAL" if 'VIRTUAL' in col['EXTRA'] else "STORED" if 'STORED' in col['EXTRA'] else None,
                expression=col['GENERATION_EXPRESSION'],

                server_default=col['COLUMN_DEFAULT'],
                set=self._parse_type(col['COLUMN_TYPE']) if col['DATA_TYPE'] in ['enum', 'set'] else None,
                length=col.get('CHARACTER_MAXIMUM_LENGTH', None),
                indexes=column_indexes,
                is_auto_increment='auto_increment' in col['EXTRA'],

                numeric_precision=self._parse_type(col['COLUMN_TYPE']) if col['DATA_TYPE'] in [
                    "int", "tinyint", "smallint", "mediumint", "bigint"
                ] else col.get('NUMERIC_PRECISION', None),

                numeric_scale=col.get('NUMERIC_SCALE', None),
                datetime_precision=col.get('DATETIME_PRECISION', None)
            )

    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> Iterator[Dict]:
        query = f"SELECT * FROM `{table.database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)
        results = self.cursor.fetchall()

        for row in results:
            yield dict(row)

    def _add_column(self, table: SQLTable, column: SQLColumn):
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` ADD COLUMN {MariaDBStatement._get_column_definition(table, column)}"
        if column.after:
            sql += f" AFTER `{column.after}`"
        self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn):
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` MODIFY COLUMN {MariaDBStatement._get_column_definition(table, column)}"
        self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn):
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` DROP COLUMN `{column.name}`"
        self.execute(sql)

    def update_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        existing_columns = self.get_columns(database, table)
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
            for col in columns_to_add:
                self._add_column(table, col)

            for col in columns_to_modify:
                existing_col = existing_columns_map[col.name]

                if (existing_col.virtuality and not col.virtuality):
                    # La colonna era virtuale e ora diventa normale, cancella i valori
                    clear_sql = f"UPDATE `{table.schema}`.`{table.name}` SET `{col.name}` = {'NULL' if col.is_nullable else 'DEFAULT'}"
                    self.execute(clear_sql)

                self._modify_column(table, col)

            for col in columns_to_drop:
                self._drop_column(table, col)

            return True

        except Exception as ex:
            logger.error(f"Error altering table name={table.name}: {str(ex)}")
            LOG_QUERY.append(str(ex))
            return False
