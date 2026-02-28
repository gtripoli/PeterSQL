import dataclasses
from typing import Self, Optional

from helpers.logger import logger

from structures.helpers import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLFunction, SQLRecord, SQLView, SQLTrigger, SQLDatabase, SQLCheck

from structures.engines.postgresql.indextype import PostgreSQLIndexType
from structures.engines.postgresql.builder import PostgreSQLColumnBuilder, PostgreSQLIndexBuilder


@dataclasses.dataclass
class PostgreSQLDatabase(SQLDatabase):
    pass


@dataclasses.dataclass(eq=False)
class PostgreSQLTable(SQLTable):
    schema: str = None
    
    @property
    def fully_qualified_name(self):
        schema_or_db = self.schema if self.schema else self.database.name
        return self.database.context.qualify(schema_or_db, self.name)
    
    def raw_create(self) -> str:
        columns = [str(PostgreSQLColumnBuilder(column)) for column in self.columns]

        # Only PRIMARY KEY constraints can be inline in CREATE TABLE
        # Other indexes must be created separately with CREATE INDEX
        inline_constraints = []
        for index in self.indexes:
            if index.type.name == "PRIMARY":
                inline_constraints.append(str(PostgreSQLIndexBuilder(index, inline=True)))

        columns_and_constraints = columns + inline_constraints

        return f"""
            CREATE TABLE {self.fully_qualified_name} (
                {', '.join(columns_and_constraints)}
            );
            """

    def rename(self, table: Self, new_name: str) -> bool:
        new_name_quoted = self.database.context.quote_identifier(new_name)
        statement = f'ALTER TABLE {table.fully_qualified_name} RENAME TO {new_name_quoted};'
        self.database.context.execute(statement)

        return True

    def truncate(self) -> bool:
        try:
            with self.database.context.transaction() as context:
                context.execute(f'TRUNCATE TABLE {self.fully_qualified_name};')

        except Exception as ex:
            logger.error(ex, exc_info=True)

        return True

    def create(self) -> bool:
        with self.database.context.transaction() as transaction:
            transaction.execute(self.raw_create())

            # Only create non-PRIMARY indexes separately (PRIMARY is already inline in CREATE TABLE)
            for index in self.indexes:
                if index.type.name != "PRIMARY":
                    index.create()

            for foreign_key in self.foreign_keys:
                foreign_key.create()

        return True

    def alter(self) -> bool:
        original_table = next((t for t in self.database.tables if t.id == self.id), None)
        original_columns = list(original_table.columns)
        original_indexes = list(original_table.indexes)
        original_primary_keys = next((pk for pk in original_indexes if pk.type == PostgreSQLIndexType.PRIMARY), None)
        original_foreign_keys = list(original_table.foreign_keys)

        current_columns = list(self.columns)
        current_indexes = list(self.indexes)
        current_primary_keys = next((pk for pk in current_indexes if pk.type == PostgreSQLIndexType.PRIMARY), None)
        current_foreign_keys = list(self.foreign_keys)

        map_columns = merge_original_current(original_columns, current_columns)
        map_indexes = merge_original_current(original_indexes, current_indexes)
        map_foreign_keys = merge_original_current(original_foreign_keys, current_foreign_keys)

        try:
            with self.database.context.transaction() as transaction:
                if self.name != original_table.name:
                    new_name_quoted = self.database.context.quote_identifier(self.name)
                    transaction.execute(f'ALTER TABLE {original_table.fully_qualified_name} RENAME TO {new_name_quoted};')

                # Handle column changes
                for column in map_columns['added']:
                    transaction.execute(f'ALTER TABLE {self.fully_qualified_name} ADD COLUMN {str(PostgreSQLColumnBuilder(column))};')

                for column in map_columns['removed']:
                    col_name_quoted = self.database.context.quote_identifier(column.name)
                    transaction.execute(f'ALTER TABLE {self.fully_qualified_name} DROP COLUMN {col_name_quoted};')

                for column in map_columns['modified']:
                    original_column = column['original']
                    current_column = column['current']
                    if original_column.name != current_column.name:
                        old_name_quoted = self.database.context.quote_identifier(original_column.name)
                        new_name_quoted = self.database.context.quote_identifier(current_column.name)
                        transaction.execute(f'ALTER TABLE {self.fully_qualified_name} RENAME COLUMN {old_name_quoted} TO {new_name_quoted};')
                    # For other changes, might need more complex ALTER statements

                # Handle index changes
                for index in map_indexes['added']:
                    index.create()

                for index in map_indexes['removed']:
                    index.drop()

                for index in map_indexes['modified']:
                    index['current'].alter(index['original'])

                # Handle foreign key changes
                for fk in map_foreign_keys['added']:
                    fk.create()

                for fk in map_foreign_keys['removed']:
                    fk.drop()

        except Exception as ex:
            logger.error(ex, exc_info=True)
            raise

        return True

    def drop(self) -> bool:
        return self.database.context.execute(f'DROP TABLE {self.fully_qualified_name}')


@dataclasses.dataclass(eq=False)
class PostgreSQLCheck(SQLCheck):
    def create(self) -> bool:
        statement = f'ALTER TABLE {self.table.fully_qualified_name} ADD CONSTRAINT {self.quoted_name} CHECK ({self.expression})'
        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        statement = f'ALTER TABLE {self.table.fully_qualified_name} DROP CONSTRAINT {self.quoted_name}'
        return self.table.database.context.execute(statement)

    def alter(self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass(eq=False)
class PostgreSQLColumn(SQLColumn):
    def add(self) -> bool:
        statement = f'ALTER TABLE {self.table.fully_qualified_name} ADD COLUMN {str(PostgreSQLColumnBuilder(self))};'
        return self.table.database.context.execute(statement)

    def rename(self, new_name: str) -> bool:
        old_name_quoted = self.table.database.context.quote_identifier(self.name)
        new_name_quoted = self.table.database.context.quote_identifier(new_name)
        statement = f'ALTER TABLE {self.table.fully_qualified_name} RENAME COLUMN {old_name_quoted} TO {new_name_quoted};'
        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        col_name_quoted = self.table.database.context.quote_identifier(self.name)
        statement = f'ALTER TABLE {self.table.fully_qualified_name} DROP COLUMN {col_name_quoted};'
        return self.table.database.context.execute(statement)

    def modify(self, current: Self):
        statements = []
        col_name_quoted = self.table.database.context.quote_identifier(current.name)
        table_name = self.table.fully_qualified_name
        
        if self.name != current.name:
            old_name_quoted = self.table.database.context.quote_identifier(self.name)
            statements.append(f'ALTER TABLE {table_name} RENAME COLUMN {old_name_quoted} TO {col_name_quoted}')
        
        type_changed = (self.datatype != current.datatype or 
                       self.length != current.length or 
                       self.numeric_precision != current.numeric_precision)
        if type_changed:
            datatype_str = str(current.datatype.name)
            if current.datatype.has_length and current.length:
                datatype_str += f"({current.length})"
            elif current.datatype.has_precision:
                if current.datatype.has_scale and current.numeric_scale:
                    datatype_str += f"({current.numeric_precision},{current.numeric_scale})"
                elif current.numeric_precision:
                    datatype_str += f"({current.numeric_precision})"
            
            statements.append(f'ALTER TABLE {table_name} ALTER COLUMN {col_name_quoted} TYPE {datatype_str}')
        
        if self.is_nullable != current.is_nullable:
            if current.is_nullable:
                statements.append(f'ALTER TABLE {table_name} ALTER COLUMN {col_name_quoted} DROP NOT NULL')
            else:
                statements.append(f'ALTER TABLE {table_name} ALTER COLUMN {col_name_quoted} SET NOT NULL')
        
        if self.server_default != current.server_default:
            if current.server_default:
                default_stmt = f'ALTER TABLE {table_name} ALTER COLUMN {col_name_quoted} SET DEFAULT {current.server_default}'
                statements.append(default_stmt)
            else:
                statements.append(f'ALTER TABLE {table_name} ALTER COLUMN {col_name_quoted} DROP DEFAULT')
        
        for stmt in statements:
            self.table.database.context.execute(stmt)
        
        return True


@dataclasses.dataclass(eq=False)
class PostgreSQLIndex(SQLIndex):
    def create(self) -> bool:
        statement = str(PostgreSQLIndexBuilder(self, inline=False))
        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        if self.type.name == "PRIMARY":
            constraint_name_quoted = self.table.database.context.quote_identifier(self.name)
            statement = f'ALTER TABLE {self.table.fully_qualified_name} DROP CONSTRAINT {constraint_name_quoted};'
        else:
            schema_or_db = self.table.schema if self.table.schema else self.table.database.name
            index_fqn = self.table.database.context.qualify(schema_or_db, self.name)
            statement = f'DROP INDEX IF EXISTS {index_fqn};'
        return self.table.database.context.execute(statement)

    def alter(self, original_index: Self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass
class PostgreSQLForeignKey(SQLForeignKey):
    def create(self) -> bool:
        columns = ", ".join(self.table.database.context.quote_identifier(col) for col in self.columns)
        ref_columns = ", ".join(self.table.database.context.quote_identifier(col) for col in self.reference_columns)
        constraint_name_quoted = self.table.database.context.quote_identifier(self.name)
        statement = f'ALTER TABLE {self.table.fully_qualified_name} ADD CONSTRAINT {constraint_name_quoted} FOREIGN KEY ({columns}) REFERENCES {self.reference_table} ({ref_columns})'
        if self.on_update and self.on_update != "NO ACTION":
            statement += f" ON UPDATE {self.on_update}"
        if self.on_delete and self.on_delete != "NO ACTION":
            statement += f" ON DELETE {self.on_delete}"
        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        constraint_name_quoted = self.table.database.context.quote_identifier(self.name)
        statement = f'ALTER TABLE {self.table.fully_qualified_name} DROP CONSTRAINT {constraint_name_quoted}'
        return self.table.database.context.execute(statement)

    def modify(self, new: "PostgreSQLForeignKey") -> None:
        self.drop()
        new.create()


@dataclasses.dataclass
class PostgreSQLRecord(SQLRecord):
    def raw_insert_record(self) -> str:
        columns_values = {}

        for column in self.table.columns:
            if hasattr(column, 'virtuality') and column.virtuality is not None:
                continue

            value = self.values.get(column.name)
            if value is not None and str(value).strip():
                if column.datatype.format:
                    value = column.datatype.format(value)

                columns_values[self.table.database.context.quote_identifier(column.name)] = str(value)

        if not columns_values:
            raise AssertionError("No columns values")

        return f"INSERT INTO {self.table.fully_qualified_name} ({', '.join(columns_values.keys())}) VALUES ({', '.join(columns_values.values())})"

    def raw_update_record(self) -> Optional[str]:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"{self.table.database.context.quote_identifier(identifier_name)} = {identifier_value}" for identifier_name, identifier_value in identifier_columns.items()])

        sql_select = f"SELECT * FROM {self.table.fully_qualified_name} WHERE {identifier_conditions}"
        self.table.database.context.execute(sql_select)

        if not (existing_record := self.table.database.context.fetchone()):
            logger.warning(f"Record not found for update: {identifier_columns}")
            raise AssertionError("Record not found for update with identifier columns")

        changed_columns = []

        for col_name, new_value in self.values.items():
            column: SQLColumn = next((c for c in self.table.columns if c.name == col_name), None)
            existing_value = dict(existing_record).get(col_name)
            if (new_value or "") != (existing_value or ""):
                col_quoted = self.table.database.context.quote_identifier(col_name)
                if new_value is None:
                    changed_columns.append(f"{col_quoted} = NULL")
                elif column.datatype.format:
                    changed_columns.append(f"{col_quoted} = {column.datatype.format(new_value)}")
                else:
                    changed_columns.append(f"{col_quoted} = {new_value}")

        if not changed_columns:
            return None

        set_clause = ", ".join(changed_columns)

        return f"UPDATE {self.table.fully_qualified_name} SET {set_clause} WHERE {identifier_conditions}"

    def raw_delete_record(self) -> str:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"{self.table.database.context.quote_identifier(identifier_name)} = {identifier_value}" for identifier_name, identifier_value in identifier_columns.items()])

        return f"DELETE FROM {self.table.fully_qualified_name} WHERE {identifier_conditions}"

    def insert(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_insert_record := self.raw_insert_record():
                return transaction.execute(raw_insert_record)

            return False

    def update(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_update_record := self.raw_update_record():
                return transaction.execute(raw_update_record)

            return False

    def delete(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_delete_record := self.raw_delete_record():
                return transaction.execute(raw_delete_record)

            return False


@dataclasses.dataclass
class PostgreSQLView(SQLView):
    @property
    def fully_qualified_name(self):
        return self.database.context.qualify('public', self.name)
    
    def create(self) -> bool:
        statement = f'CREATE VIEW {self.fully_qualified_name} AS {self.statement};'
        return self.database.context.execute(statement)

    def drop(self) -> bool:
        statement = f'DROP VIEW IF EXISTS {self.fully_qualified_name};'
        return self.database.context.execute(statement)

    def alter(self) -> bool:
        statement = f'CREATE OR REPLACE VIEW {self.fully_qualified_name} AS {self.statement};'
        return self.database.context.execute(statement)


@dataclasses.dataclass
class PostgreSQLFunction(SQLFunction):
    parameters: str = ""
    returns: str = ""
    language: str = "plpgsql"
    volatility: str = "VOLATILE"
    statement: str = ""
    
    def create(self) -> bool:
        create_statement = f"""
            CREATE OR REPLACE FUNCTION {self.fully_qualified_name}({self.parameters})
            RETURNS {self.returns}
            LANGUAGE {self.language}
            {self.volatility}
            AS $$
            BEGIN
                {self.statement}
            END;
            $$;
        """
        return self.database.context.execute(create_statement)
    
    def drop(self) -> bool:
        statement = f'DROP FUNCTION IF EXISTS {self.fully_qualified_name}({self.parameters});'
        return self.database.context.execute(statement)
    
    def alter(self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass
class PostgreSQLTrigger(SQLTrigger):
    def create(self) -> bool:
        return self.database.context.execute(self.statement)

    def alter(self) -> bool:
        self.drop()
        return self.create()

    def drop(self) -> bool:
        import re
        
        trigger_name_quoted = self.database.context.quote_identifier(self.name)
        
        match = re.search(r'CREATE\s+TRIGGER\s+\S+\s+.*?\s+ON\s+(\S+\.\S+|\S+)', self.statement, re.IGNORECASE | re.DOTALL)
        if match:
            table_name = match.group(1)
            statement = f'DROP TRIGGER IF EXISTS {trigger_name_quoted} ON {table_name};'
        else:
            statement = f'DROP TRIGGER IF EXISTS {trigger_name_quoted};'
        
        return self.database.context.execute(statement)
