import re
import pymysql

from typing import Dict, Optional, List, Any

from helpers.logger import logger

from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord
from models.structures.statement import AbstractStatement, Transaction, LOG_QUERY, AbstractColumnBuilder
from models.structures.mariadb.datatype import MariaDBDataType

from models.structures.mariadb.indextype import MariaDBIndexType


class MariaDBColumnDefinition(AbstractColumnBuilder):
    """MariaDB/MySQL-specific column definition builder."""

    TEMPLATE = ["%(name)s", "%(datatype)s", "%(unsigned)s", "%(zerofill)s", "%(nullable)s", "%(auto_increment)s", "%(default)s", "%(comment)s"]

    def _build_parts(self) -> Dict[str, str]:
        # Get base parts from parent
        parts = super()._build_parts()

        # MariaDB-specific datatype modifications
        datatype = parts['datatype']
        if self.column.datatype.has_unsigned and self.column.is_unsigned:
            datatype += ' UNSIGNED'
        if self.column.datatype.has_zerofill and self.column.is_zerofill:
            datatype += ' ZEROFILL'
        parts['datatype'] = datatype

        # Add syntax-specific parts
        if self.column.is_auto_increment:
            parts['auto_increment'] = f"AUTO_INCREMENT"

        return parts


class MariaDBSyntax:
    AUTO_INCREMENT = "AUTO_INCREMENT"


class MariaDBStatement(AbstractStatement):
    _column_builder = MariaDBColumnDefinition

    def __init__(self, session):
        self.hostname = session.configuration.hostname
        self.port = session.configuration.port
        self.username = session.configuration.username
        self.password = session.configuration.password
        self.database = getattr(session.configuration, 'database', None)

        self.connection_url = f"mariadb://{self.username}:{self.password}@{self.hostname}:{self.port}"
        if self.database:
            self.connection_url += f"/{self.database}"

        super().__init__(self.connection_url)

    def connect(self, **connect_kwargs) -> None:
        if self._connection is None:
            try:
                self._connection = pymysql.connect(
                    host=self.hostname,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                self._cursor = self._connection.cursor()
                self._on_connect()
            except Exception as e:
                logger.error(f"Failed to connect to MariaDB: {e}")
                raise

    def _on_connect(self, *args, **kwargs):
        super()._on_connect(*args, **kwargs)
        # Enable foreign key checks
        self.execute("SET FOREIGN_KEY_CHECKS = 1")

    def get_server_version(self) -> str:
        self.execute("SELECT VERSION()")
        version = self.cursor.fetchone()
        return version['VERSION()']

    def get_server_uptime(self) -> Optional[int]:
        self.execute("SHOW STATUS LIKE 'Uptime'")
        result = self.cursor.fetchone()
        return int(result['Value']) if result else None

    # databases
    def get_databases(self) -> List[SQLDatabase]:
        self.execute("SHOW DATABASES")
        databases = self.cursor.fetchall()
        return [
            SQLDatabase(id=i, name=db['Database'], get_tables_handler=self.get_tables)
            for i, db in enumerate(databases)
        ]

    # TABLES
    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        logger.debug("get_tables")

        LOG_QUERY.append(f"/* get_tables */")
        self.execute("""
            SELECT TABLE_NAME, TABLE_TYPE, ENGINE, TABLE_COLLATION, CREATE_TIME, UPDATE_TIME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        """, (database.name,))

        tables_result = self.cursor.fetchall()

        results = []
        for i, row in enumerate(tables_result):
            results.append(
                SQLTable(
                    id=i,  # MariaDB doesn't have a simple ID
                    name=row['TABLE_NAME'],
                    database=database,
                    engine=row['ENGINE'],
                    get_columns_handler=self.get_columns,
                    get_indexes_handler=self.get_indexes,
                    get_foreign_keys_handler=self.get_foreign_keys,
                    table_collation=row['TABLE_COLLATION'],
                    create_time=row['CREATE_TIME'],
                    update_time=row['UPDATE_TIME'],
                )
            )

        return results

    def build_empty_table(self, database: SQLDatabase):
        return SQLTable(
            id=-1,
            name='',
            database=database,
            engine='InnoDB',
            get_indexes_handler=self.get_indexes,
            get_columns_handler=self.get_columns,
            get_foreign_keys_handler=self.get_foreign_keys,
        )

    def rename_table(self, table: SQLTable, name: str) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` RENAME TO `{table.database.name}`.`{name}`"
        return self.execute(sql)

    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        column_definition = [str(self._column_builder(c)) for c in table.columns]

        constraints = []

        # Primary key
        pk = next((idx for idx in table.indexes if idx.type == MariaDBIndexType.PRIMARY), None)
        if pk and pk.columns:
            cols = ", ".join([f"`{c}`" for c in pk.columns])
            constraints.append(f"PRIMARY KEY ({cols})")

        # Unique indexes
        for idx in table.indexes:
            if idx.type == MariaDBIndexType.UNIQUE:
                cols = ", ".join([f"`{c}`" for c in idx.columns])
                constraints.append(f"UNIQUE KEY `{idx.name}` ({cols})")

        # Foreign keys
        for fk in table.foreign_keys:
            cols = ", ".join([f"`{c}`" for c in fk.columns])
            ref_cols = ", ".join([f"`{c}`" for c in fk.reference_columns])
            constraint = f"CONSTRAINT `{fk.name}` FOREIGN KEY ({cols}) REFERENCES `{fk.reference_table}` ({ref_cols})"
            if fk.on_update and fk.on_update != "NO ACTION":
                constraint += f" ON UPDATE {fk.on_update}"
            if fk.on_delete and fk.on_delete != "NO ACTION":
                constraint += f" ON DELETE {fk.on_delete}"
            constraints.append(constraint)

        engine = table.engine or 'InnoDB'
        collation = table.table_collation or 'utf8mb4_general_ci'

        sql = f"CREATE TABLE `{database.name}`.`{table.name}` ({', '.join(column_definition + constraints)}) ENGINE={engine} DEFAULT CHARSET=utf8mb4 COLLATE={collation}"

        return self.execute(sql)

    def alter_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        original_table = next((t for t in database.tables if t.id == table.id), None)
        original_columns = list(original_table.columns)
        original_indexes = list(original_table.indexes)
        original_foreign_keys = list(original_table.foreign_keys)

        table_columns = list(table.columns)
        table_indexes = list(table.indexes)
        table_foreign_keys = list(table.foreign_keys)

        original_column_map = {col.name: col for col in original_columns}
        table_column_map = {col.name: col for col in table_columns}
        original_index_map = {idx.name: idx for idx in original_indexes}
        table_index_map = {idx.name: idx for idx in table_indexes}
        original_fk_map = {fk.name: fk for fk in original_foreign_keys}
        table_fk_map = {fk.name: fk for fk in table_foreign_keys}

        try:
            with Transaction(self):
                # Rename table if name changed
                if table.name != original_table.name:
                    self.rename_table(original_table, table.name)

                # Add new columns
                for col_name, col in table_column_map.items():
                    if col_name not in original_column_map:
                        self._add_column(table, col)

                # Modify existing columns
                for col_name, col in table_column_map.items():
                    if col_name in original_column_map:
                        original_col = original_column_map[col_name]
                        if col != original_col:
                            self._modify_column(table, col)

                # Rename columns (if name changed) - Note: MySQL doesn't support direct column rename in MODIFY
                # Column renames are handled by comparing names, but since we're using name as key, renames would appear as drop/add

                # Drop removed columns
                for col_name, original_col in original_column_map.items():
                    if col_name not in table_column_map:
                        self._drop_column(table, original_col)

                # Handle index changes
                # Add new indexes
                for idx_name, idx in table_index_map.items():
                    if idx_name not in original_index_map:
                        self._create_index(table, idx)
                    elif idx != original_index_map[idx_name]:
                        self._drop_index(table, original_index_map[idx_name])
                        self._create_index(table, idx)

                # Drop removed indexes
                for idx_name, idx in original_index_map.items():
                    if idx_name not in table_index_map:
                        self._drop_index(table, idx)

                # Handle foreign key changes
                # Add new foreign keys
                for fk_name, fk in table_fk_map.items():
                    if fk_name not in original_fk_map:
                        self._add_foreign_key(table, fk)

                # Modify existing foreign keys
                for fk_name, fk in table_fk_map.items():
                    if fk_name in original_fk_map and fk != original_fk_map[fk_name]:
                        self._drop_foreign_key(table, original_fk_map[fk_name])
                        self._add_foreign_key(table, fk)

                # Drop removed foreign keys
                for fk_name, fk in original_fk_map.items():
                    if fk_name not in table_fk_map:
                        self._drop_foreign_key(table, fk)

        except Exception as e:
            logger.error(f"Error altering table {table.name}: {e}")
            return False

        return True

    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        sql = f"DROP TABLE `{database.name}`.`{table.name}`"
        return self.execute(sql)

    # COLUMNS
    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        if table.id == -1:
            return []
        logger.debug("get columns")
        LOG_QUERY.append(f"/* get_columns */")

        self.execute(f"""
            SELECT ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT,
                   CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE,
                   EXTRA, COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{table.database.name}' AND TABLE_NAME = '{table.name}'
            ORDER BY ORDINAL_POSITION
        """)

        results = []
        for col in self.cursor.fetchall():
            parsed_type = MariaDBStatement.parse_type(col['COLUMN_TYPE'].upper())

            results.append(
                SQLColumn(
                    id=col['ORDINAL_POSITION'],
                    name=col['COLUMN_NAME'],
                    datatype=MariaDBDataType.get_by_name(col),
                    is_nullable=col['IS_NULLABLE'] == 'YES',
                    table=table,
                    # is_primary_key=col['COLUMN_KEY'] == 'PRI',
                    server_default=col['COLUMN_DEFAULT'],
                    is_auto_increment='auto_increment' in col['EXTRA'].lower(),
                    length=parsed_type.length,
                    numeric_precision=parsed_type.precision,
                    numeric_scale=parsed_type.scale,
                    set=parsed_type.set,
                    is_unsigned=parsed_type.is_unsigned,
                    is_zerofill=parsed_type.is_zerofill,
                )
            )

        return results

    def _add_column(self, table: SQLTable, column: SQLColumn) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` ADD COLUMN {MariaDBStatement.build_column_definition(table, column)}"
        return self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` MODIFY COLUMN {MariaDBStatement.build_column_definition(table, column)}"
        return self.execute(sql)

    def _rename_column(self, table: SQLTable, column: SQLColumn, new_name: str) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` CHANGE COLUMN `{column.name}` `{new_name}` {MariaDBStatement.build_column_definition(table, column)}"
        return self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` DROP COLUMN `{column.name}`"
        return self.execute(sql)

    # INDEXES
    def get_indexes(self, table: SQLTable) -> List[SQLIndex]:
        if table.id == -1:
            return []
        logger.debug("get_indexes")

        LOG_QUERY.append("/* get_indexes */")

        results = []

        # Get primary keys
        self.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """, (table.database.name, table.name))

        pk_columns = [row['COLUMN_NAME'] for row in self.cursor.fetchall()]
        if pk_columns:
            results.append(
                SQLIndex(
                    id=0,
                    name="PRIMARY",
                    type=MariaDBIndexType.PRIMARY,
                    columns=pk_columns,
                )
            )

        # Get other indexes
        self.execute("""
            SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE, INDEX_TYPE
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND INDEX_NAME != 'PRIMARY'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """, (table.database.name, table.name))

        indexes = {}
        for row in self.cursor.fetchall():
            index_name = row['INDEX_NAME']
            if index_name not in indexes:
                is_unique = not row['NON_UNIQUE']
                index_type_name = row['INDEX_TYPE'].upper()
                if index_type_name == 'FULLTEXT':
                    index_type = MariaDBIndexType.FULLTEXT
                elif index_type_name == 'SPATIAL':
                    index_type = MariaDBIndexType.SPATIAL
                elif is_unique:
                    index_type = MariaDBIndexType.UNIQUE
                else:
                    index_type = MariaDBIndexType.NORMAL

                indexes[index_name] = SQLIndex(
                    id=0,
                    name=index_name,
                    type=index_type,
                    columns=[],
                )
            indexes[index_name].columns.append(row['COLUMN_NAME'])

        results.extend(indexes.values())

        return results

    def _create_index(self, table: SQLTable, index: SQLIndex) -> bool:
        if index.type == MariaDBIndexType.PRIMARY:
            return False  # PRIMARY is handled in table creation

        index_type = ""
        if index.type == MariaDBIndexType.FULLTEXT:
            index_type = "FULLTEXT"
        elif index.type == MariaDBIndexType.SPATIAL:
            index_type = "SPATIAL"

        unique = "UNIQUE" if index.type == MariaDBIndexType.UNIQUE else ""

        cols = ", ".join([f"`{c}`" for c in index.columns])

        sql = f"CREATE {unique} {index_type} INDEX `{index.name}` ON `{table.database.name}`.`{table.name}` ({cols})"
        return self.execute(sql)

    def _drop_index(self, table: SQLTable, index: SQLIndex) -> bool:
        sql = f"DROP INDEX `{index.name}` ON `{table.database.name}`.`{table.name}`"
        return self.execute(sql)

    # FOREIGN KEYS
    def get_foreign_keys(self, table: SQLTable) -> List[SQLForeignKey]:
        if table.id == -1:
            return []
        logger.debug("get_foreign_keys")

        LOG_QUERY.append("/* get_foreign_keys */")

        self.execute("""
            SELECT 
                kcu.CONSTRAINT_NAME,
                GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION) as COLUMNS,
                kcu.REFERENCED_TABLE_NAME,
                GROUP_CONCAT(REFERENCED_COLUMN_NAME ORDER BY ORDINAL_POSITION) as REFERENCED_COLUMNS,
                UPDATE_RULE,
                DELETE_RULE
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            WHERE kcu.TABLE_SCHEMA = %s AND kcu.TABLE_NAME = %s
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            GROUP BY CONSTRAINT_NAME
        """, (table.database.name, table.name))

        results = []
        for i, fk in enumerate(self.cursor.fetchall(), 1):
            results.append(
                SQLForeignKey(
                    id=i,
                    name=fk['CONSTRAINT_NAME'],
                    columns=fk['COLUMNS'].split(','),
                    reference_table=fk['REFERENCED_TABLE_NAME'],
                    reference_columns=fk['REFERENCED_COLUMNS'].split(','),
                    on_update=fk['UPDATE_RULE'],
                    on_delete=fk['DELETE_RULE'],
                )
            )

        return results

    def _add_foreign_key(self, table: SQLTable, foreign_key: SQLForeignKey) -> bool:
        cols = ", ".join([f"`{c}`" for c in foreign_key.columns])
        ref_cols = ", ".join([f"`{c}`" for c in foreign_key.reference_columns])
        constraint = f"ADD CONSTRAINT `{foreign_key.name}` FOREIGN KEY ({cols}) REFERENCES `{foreign_key.reference_table}` ({ref_cols})"
        if foreign_key.on_update and foreign_key.on_update != "NO ACTION":
            constraint += f" ON UPDATE {foreign_key.on_update}"
        if foreign_key.on_delete and foreign_key.on_delete != "NO ACTION":
            constraint += f" ON DELETE {foreign_key.on_delete}"
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` {constraint}"
        return self.execute(sql)

    def _drop_foreign_key(self, table: SQLTable, foreign_key: SQLForeignKey) -> bool:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` DROP FOREIGN KEY `{foreign_key.name}`"
        return self.execute(sql)

    # RECORDS
    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[SQLRecord]:
        LOG_QUERY.append("/* get_records */")
        query = f"SELECT * FROM `{table.database.name}`.`{table.name}` LIMIT {limit} OFFSET {offset}"
        self.execute(query)

        results = []
        for i, record in enumerate(self.cursor.fetchall(), start=offset):
            results.append(
                SQLRecord(_id=i, table=table, **record)
            )
        return results

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
            for record in records :
                if raw_delete_record := self.raw_delete_record(database, table, record):
                    results.append( self.execute(raw_delete_record))

        return all(results)
