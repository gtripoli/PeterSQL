import re
import abc
import uuid

from typing import Dict, Any, Optional, List, NamedTuple, Type

from helpers.logger import logger
from helpers.observables import ObservableArray

from models.structures.database import SQLDatabase, SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord

LOG_QUERY: ObservableArray[str] = ObservableArray()

class AbstractColumnBuilder(abc.ABC):
    TEMPLATE: str

    parts: Dict[str, str]

    def __init__(self, column: SQLColumn):
        self.column = column

        self.parts = {
            'name': self.name,
            'datatype': self.datatype,
            'nullable': self.nullable,
            'default': self.default,
            'collate': self.collation,
            'comment': self.comment,
            'virtual': self.virtual,
            'unsigned': self.unsigned,
            'zerofill': self.zerofill,
            'primary_key': self.primary_key,
            # 'unique': self.unique,
            'auto_increment': self.auto_increment,
            'check': self.check,
            # 'generated': self.generated,
            # 'references': self.references,
            # 'constraint': self.constraint,
        }

    @property
    def name(self):
        return f"`{self.column.name}`"

    @property
    def datatype(self):
        datatype_str = str(self.column.datatype.name)

        if self.column.datatype.has_length:
            datatype_str += f"({self.column.length or self.column.datatype.default_length})"

        if self.column.datatype.has_precision:
            if self.column.datatype.has_scale:
                datatype_str += f"({self.column.numeric_precision or self.column.datatype.default_precision},{self.column.numeric_scale or self.column.datatype.default_scale})"
            else:
                datatype_str += f"({self.column.numeric_precision or self.column.datatype.default_precision})"

        if self.column.datatype.has_set:
            datatype_str += f"""('{"','".join(list(set(self.column.set or self.column.datatype.default_set)))}')"""

        return datatype_str

    @property
    def auto_increment(self):
        return 'AUTO_INCREMENT' if self.column.is_auto_increment else ''

    @property
    def nullable(self):
        return 'NOT NULL' if not self.column.is_nullable or self.column.is_auto_increment else 'NULL'

    @property
    def default(self):
        return f"DEFAULT {self.column.server_default}" if self.column.server_default and self.column.server_default != '' else ''

    @property
    def collation(self):
        return f"COLLATE {self.column.collation_name}" if self.column.collation_name else ''

    @property
    def check(self):
        return f"CHECK ({self.column.set})" if self.column.datatype.has_set else ''

    @property
    def comment(self):
        return f"COMMENT '{self.column.comment}'" if self.column.comment else ''

    @property
    def virtual(self):
        return f"AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality and self.column.expression else ''

    @property
    def unsigned(self):
        return 'UNSIGNED' if self.column.is_unsigned else ''

    @property
    def zerofill(self):
        return 'ZEROFILL' if self.column.is_zerofill else ''

    @property
    def primary_key(self):
        return 'PRIMARY KEY' if self.column.is_primary_key else ''

    # @property
    # def unique(self):
    #     return 'UNIQUE' if self.column.is_unique else ''

    # @property
    # def references(self):
    #     return f"REFERENCES {self.column.references}" if self.column.references else ''

    # @property
    # def constraint(self):
    #     return f"CONSTRAINT {self.column.constraint}" if self.column.constraint else ''


    def __str__(self) -> str:
        formatted_parts = []
        for template_part in self.TEMPLATE:
            formatted = template_part % self.parts
            if formatted.strip():  # Only include non-empty parts
                formatted_parts.append(formatted.strip())

        return " ".join(formatted_parts)


class AbstractStatement(abc.ABC):
    _connection: Any = None
    _cursor: Any = None

    _column_builder: Type[AbstractColumnBuilder]

    def __init__(self, connection_url):
        self.connection_url = connection_url

    @abc.abstractmethod
    def connect(self, **connect_kwargs) -> None:
        """Establish connection to the database using native driver"""
        raise NotImplementedError

    def disconnect(self) -> None:
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None

        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> Any:
        if self._connection is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._connection

    @property
    def cursor(self) -> Any:
        if self._cursor is None:
            raise RuntimeError("Not connected to the database. Call connect() first.")
        return self._cursor

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _on_connect(self, *args, **kwargs):
        logger.debug("connected")

    def _on_disconnect(self, *args, **kwargs):
        logger.debug("disconnected")

    @staticmethod
    def generate_uuid(length: int = 8) -> str:
        return str(uuid.uuid4())[::-1][:length]

    @abc.abstractmethod
    def get_server_version(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_server_uptime(self) -> Optional[int]:
        raise NotImplementedError

    # DATABASE ABSTRACT METHODS
    @abc.abstractmethod
    def get_databases(self) -> List[SQLDatabase]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tables(self, database: SQLDatabase) -> List[SQLTable]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_columns(self, table: SQLTable) -> List[SQLColumn]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_indexes(self, table: SQLTable) -> List[SQLIndex]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_foreign_keys(self, table: SQLTable) -> List[SQLForeignKey]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_records(self, table: SQLTable, limit: int = 1000, offset: int = 0) -> List[SQLRecord]:
        raise NotImplementedError

    # TABLE ABSTRACT METHODS
    @abc.abstractmethod
    def build_empty_table(self, database: SQLDatabase) -> SQLTable:
        raise NotImplementedError

    @abc.abstractmethod
    def create_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def alter_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def drop_table(self, database: SQLDatabase, table: SQLTable) -> bool:
        raise NotImplementedError

    def save_table(self, database: SQLDatabase, table: SQLTable) -> Optional[bool]:
        if not table:
            return

        if table.id == -1:
            method = self.create_table
        else:
            method = self.alter_table

        result = method(database, table)
        database.tables.clear()

        return result

    # COLUMN METHODS
    def _add_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` ADD COLUMN {self.build_column_definition(table, column)}"
        if hasattr(column, 'after') and column.after:
            sql += f" AFTER `{column.after}`"
        self.execute(sql)

    def _modify_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` MODIFY COLUMN {self.build_column_definition(table, column)}"
        self.execute(sql)

    def _drop_column(self, table: SQLTable, column: SQLColumn) -> None:
        sql = f"ALTER TABLE `{table.database.name}`.`{table.name}` DROP COLUMN `{column.name}`"
        self.execute(sql)

    def _get_identifier_columns(self, table: SQLTable, record: SQLRecord) -> Dict[str, str]:
        identifier_indexes = table.get_identifier_indexes()

        if not identifier_indexes:
            raise ValueError("Cannot identify record without primary or unique index")

        identifier_conditions = {}
        for identifier_index in identifier_indexes:
            columns: List[SQLColumn] = [column for column in table.columns if column.name in identifier_index.columns]
            original_record = next((r for r in list(table.records) if r.id == record.id), None)
            for column in columns:
                identifier_conditions[column.name] = column.datatype.format(getattr(original_record, column.name))

            if identifier_index.type.is_primary:
                break

        return identifier_conditions

    # RECORD ABSTRACT METHODS
    def raw_insert_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> str:
        columns_values = {}

        for column in table.columns:
            value = getattr(record, column.name)
            if (value := column.datatype.format(value)) is not None:
                columns_values[column.name] = str(value)

        if not columns_values:
            assert False, "No columns values"

        return f"""INSERT INTO `{database.name}`.`{table.name}` ({','.join(columns_values.keys())}) VALUES ({','.join(columns_values.values())})"""

    def raw_update_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> Optional[str]:
        identifier_columns = self._get_identifier_columns(table, record)

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        sql_select = f"SELECT * FROM `{database.name}`.`{table.name}` WHERE {identifier_conditions}"
        self.execute(sql_select)

        if not (existing_record := self.cursor.fetchone()):
            logger.warning(f"Record not found for update: {identifier_columns}")
            assert False, "Record not found for update with identifier columns"

        changed_columns = []

        for col_name, new_value in record._data.items():
            column: SQLColumn = next((c for c in table.columns if c.name == col_name), None)
            existing_value = dict(existing_record).get(col_name)
            if (new_value or "") != (existing_value or ""):
                if new_value is None:
                    changed_columns.append(f"`{col_name}` = NULL")
                else:
                    changed_columns.append(f"`{col_name}` = {column.datatype.format(new_value)}")

        if not changed_columns:
            return None

        set_clause = ", ".join(changed_columns)

        return f"UPDATE `{database.name}`.`{table.name}` SET {set_clause} WHERE {identifier_conditions}"

    def raw_delete_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> str:
        identifier_columns = self._get_identifier_columns(table, record)

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        return f"DELETE FROM `{database.name}`.`{table.name}` WHERE {identifier_conditions}"

    @abc.abstractmethod
    def insert_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def update_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def delete_records(self, database: SQLDatabase, table: SQLTable, records: List[SQLRecord]) -> bool:
        raise NotImplementedError

    def save_record(self, database: SQLDatabase, table: SQLTable, record: SQLRecord) -> Optional[bool]:
        if not isinstance(record, SQLRecord):
            raise ValueError("save_record now expects SQLRecord instance")

        if not record.is_valid():
            raise ValueError("Record is not yet valid")

        if record.is_new():
            method = self.insert_record
        else:
            method = self.update_record

        return method(database, table, record)

    # EXECUTION
    def execute(self, query: str, params=None, **kwargs) -> bool:
        query = re.sub(r'\s+', ' ', str(query)).strip()

        LOG_QUERY.append(query)

        try:
            if params is not None:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query, **kwargs)

        except Exception as ex:
            logger.error(ex, exc_info=True)
            LOG_QUERY.append(f"/* {str(ex)} */")
            raise

        return True


class Transaction:
    def __init__(self, statement: AbstractStatement):
        self.statement = statement

    def __enter__(self):
        self.statement.execute("BEGIN")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.statement.execute("COMMIT")
            logger.info("Transaction committed")
        else:
            self.statement.execute("ROLLBACK")
            logger.error(f"Transaction failed: {exc_val}")
            LOG_QUERY.append(f"/* {str(exc_val)} */")
