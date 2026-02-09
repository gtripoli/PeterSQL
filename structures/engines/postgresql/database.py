import dataclasses
from typing import Self, Optional

from helpers.logger import logger

from structures.helpers import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase

from structures.engines.postgresql.indextype import PostgreSQLIndexType
from structures.engines.postgresql.builder import PostgreSQLColumnBuilder, PostgreSQLIndexBuilder


@dataclasses.dataclass
class PostgreSQLDatabase(SQLDatabase):
    pass


@dataclasses.dataclass(eq=False)
class PostgreSQLTable(SQLTable):
    schema: str = None
    def raw_create(self) -> str:
        columns = [str(PostgreSQLColumnBuilder(column)) for column in self.columns]

        indexes = [str(PostgreSQLIndexBuilder(index)) for index in self.indexes]

        columns_and_indexes = columns + indexes

        return f"""
            CREATE TABLE "{self.database.name}"."{self.name}" (
                {', '.join(columns_and_indexes)}
            );
            """

    def rename(self, table: Self, new_name: str) -> bool:
        sql = f'ALTER TABLE "{self.database.name}"."{table.name}" RENAME TO "{new_name}";'
        self.database.context.execute(sql)

        return True

    def truncate(self):
        try:
            with self.database.context.transaction() as context:
                context.execute(f'TRUNCATE TABLE "{self.database.name}"."{self.name}";')

        except Exception as ex:
            logger.error(ex, exc_info=True)

        return True

    def create(self) -> bool:
        with self.database.context.transaction() as transaction:
            transaction.execute(self.raw_create())

            for index in self.indexes:
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
                    transaction.execute(f'ALTER TABLE "{original_table.database.name}"."{original_table.name}" RENAME TO "{self.name}";')

                # Handle column changes
                for column in map_columns['added']:
                    transaction.execute(f'ALTER TABLE "{self.database.name}"."{self.name}" ADD COLUMN {str(PostgreSQLColumnBuilder(column))};')

                for column in map_columns['removed']:
                    transaction.execute(f'ALTER TABLE "{self.database.name}"."{self.name}" DROP COLUMN "{column.name}";')

                for column in map_columns['modified']:
                    original_column = column['original']
                    current_column = column['current']
                    if original_column.name != current_column.name:
                        transaction.execute(f'ALTER TABLE "{self.database.name}"."{self.name}" RENAME COLUMN "{original_column.name}" TO "{current_column.name}";')
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

    def drop(self):
        pass


@dataclasses.dataclass(eq=False)
class PostgreSQLColumn(SQLColumn):
    pass


@dataclasses.dataclass
class PostgreSQLIndex(SQLIndex):
    def create(self):
        sql = str(PostgreSQLIndexBuilder(self))
        self.table.database.context.execute(sql)

    def drop(self):
        if self.type.name == "PRIMARY":
            sql = f'ALTER TABLE "{self.table.database.name}"."{self.table.name}" DROP CONSTRAINT "{self.name}";'
        else:
            sql = f'DROP INDEX IF EXISTS "{self.table.database.name}"."{self.name}";'
        self.table.database.context.execute(sql)

    def alter(self, original_index: Self):
        self.drop()
        self.create()


@dataclasses.dataclass
class PostgreSQLForeignKey(SQLForeignKey):
    def create(self):
        columns = ", ".join(f'"{col}"' for col in self.columns)
        ref_columns = ", ".join(f'"{col}"' for col in self.reference_columns)
        sql = f'ALTER TABLE "{self.table.database.name}"."{self.table.name}" ADD CONSTRAINT "{self.name}" FOREIGN KEY ({columns}) REFERENCES "{self.reference_table}" ({ref_columns});'
        self.table.database.context.execute(sql)

    def drop(self):
        sql = f'ALTER TABLE "{self.table.database.name}"."{self.table.name}" DROP CONSTRAINT "{self.name}";'
        self.table.database.context.execute(sql)


@dataclasses.dataclass
class PostgreSQLRecord(SQLRecord):
    def insert(self):
        columns = ", ".join(f'"{k}"' for k in self.values.keys())
        placeholders = ", ".join("%s" for _ in self.values)
        sql = f'INSERT INTO "{self.table.database.name}"."{self.table.name}" ({columns}) VALUES ({placeholders});'
        self.table.database.context.execute(sql, tuple(self.values.values()))

    def update(self):
        set_clause = ", ".join(f'"{k}" = %s' for k in self.values.keys())
        sql = f'UPDATE "{self.table.database.name}"."{self.table.name}" SET {set_clause} WHERE id = %s;'
        self.table.database.context.execute(sql, tuple(self.values.values()) + (self.id,))

    def delete(self):
        sql = f'DELETE FROM "{self.table.database.name}"."{self.table.name}" WHERE id = %s;'
        self.table.database.context.execute(sql, (self.id,))


@dataclasses.dataclass
class PostgreSQLView(SQLView):
    def create(self):
        sql = f'CREATE VIEW "{self.database.name}"."{self.name}" AS {self.sql};'
        self.database.context.execute(sql)

    def alter(self):
        sql = f'CREATE OR REPLACE VIEW "{self.database.name}"."{self.name}" AS {self.sql};'
        self.database.context.execute(sql)

    def drop(self):
        sql = f'DROP VIEW IF EXISTS "{self.database.name}"."{self.name}";'
        self.database.context.execute(sql)


@dataclasses.dataclass
class PostgreSQLTrigger(SQLTrigger):
    def create(self):
        self.database.context.execute(self.sql)

    def alter(self):
        self.drop()
        self.create()

    def drop(self):
        sql = f'DROP TRIGGER IF EXISTS "{self.name}" ON "{self.database.name}";'
        self.database.context.execute(sql)
