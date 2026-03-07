import dataclasses
from typing import Self, Optional, Literal, Union

from helpers.logger import logger

from structures.helpers import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLCheck, SQLColumn, SQLIndex, SQLView, SQLRecord, SQLTrigger, SQLFunction, SQLDatabase, SQLForeignKey, SQLProcedure

from structures.engines.mariadb.indextype import MariaDBIndexType
from structures.engines.mariadb.builder import MariaDBColumnBuilder, MariaDBIndexBuilder


@dataclasses.dataclass
class MariaDBDatabase(SQLDatabase):
    default_collation: str = None


@dataclasses.dataclass(eq=False)
class MariaDBTable(SQLTable):
    def raw_create(self) -> str:
        columns = [str(MariaDBColumnBuilder(column)) for column in self.columns]

        indexes = [str(MariaDBIndexBuilder(index)) for index in self.indexes]

        columns_and_indexes = columns + indexes

        return f"""
            CREATE TABLE {self.fully_qualified_name} (
                {', '.join(columns_and_indexes)}
            )
            COLLATE='{self.collation_name}'
            ENGINE={self.engine};
            """

    def alter_auto_increment(self, auto_increment: int):
        statement = f"ALTER TABLE {self.fully_qualified_name} AUTO_INCREMENT {auto_increment};"
        self.database.context.execute(statement)

        return True

    def alter_collation(self, collation_name, convert: bool = True):
        charset = ""
        if convert:
            charset = f"CONVERT TO CHARACTER SET {self.database.context.COLLATIONS[collation_name]}"
        return self.database.context.execute(f"""ALTER TABLE {self.fully_qualified_name} {charset} COLLATE {collation_name};""")

    def alter_engine(self, engine: str):
        statement = f"ALTER TABLE {self.fully_qualified_name} ENGINE {engine};"
        self.database.context.execute(statement)

        return True

    def rename(self, table: Self, new_name: str) -> bool:
        statement = f"ALTER TABLE {table.fully_qualified_name} RENAME TO `{new_name}`;"
        self.database.context.execute(statement)

        return True

    def truncate(self):
        try:
            with self.database.context.transaction() as context:
                context.execute(f"TRUNCATE TABLE {self.fully_qualified_name};")

        except Exception as ex:
            logger.error(ex, exc_info=True)

        return True

    def create(self) -> bool:
        with self.database.context.transaction() as transaction:
            transaction.execute(self.raw_create())

            # Indexes are already included in raw_create() via MariaDBIndexBuilder
            # Only create foreign keys separately
            for foreign_key in self.foreign_keys:
                foreign_key.create()

        return True

    def alter(self) -> bool:
        original_table = next((t for t in self.database.tables if t.id == self.id), None)
        original_columns = list(original_table.columns)
        original_indexes = list(original_table.indexes)
        original_primary_keys = next((pk for pk in original_indexes if pk.type == MariaDBIndexType.PRIMARY), None)
        original_foreign_keys = list(original_table.foreign_keys)

        current_columns = list(self.columns)
        current_indexes = list(self.indexes)
        current_primary_keys = next((pk for pk in current_indexes if pk.type == MariaDBIndexType.PRIMARY), None)
        current_foreign_keys = list(self.foreign_keys)

        map_columns = merge_original_current(original_columns, current_columns)
        map_indexes = merge_original_current(original_indexes, current_indexes)
        map_foreign_keys = merge_original_current(original_foreign_keys, current_foreign_keys)

        try:
            with self.database.context.transaction() as transaction:
                if self.name != original_table.name:
                    self.rename(original_table, self.name)
                if self.auto_increment != original_table.auto_increment:
                    original_table.alter_auto_increment(self.auto_increment)
                if self.collation_name != original_table.collation_name:
                    original_table.alter_collation(self.collation_name)
                if self.engine != original_table.engine:
                    original_table.alter_engine(self.engine)

                for i, (original, current) in enumerate(map_columns):
                    if original is None:
                        current.add()
                    elif current is None:
                        original.drop()
                    elif current != original:
                        original.change(current)
                    elif current_columns[i] != original_columns[i]:
                        original.modify(current, original_columns[i - 1])

                for original_index, current_index in map_indexes:
                    if current_index is None:
                        original_index.drop()
                    elif original_index is None:
                        current_index.create()
                    elif original_index != current_index:
                        original_index.modify(current_index)

                for original_foreign_key, current_foreign_key in map_foreign_keys:
                    if current_foreign_key is None:
                        original_foreign_key.drop()
                    elif original_foreign_key is None:
                        current_foreign_key.create()
                    elif original_foreign_key != current_foreign_key:
                        original_foreign_key.modify(current_foreign_key)

        except Exception as ex:
            QUERY_LOGS.append(f"/* alter_table exception: {ex} */")
            logger.error(ex, exc_info=True)
            raise

        return True

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TABLE {self.fully_qualified_name}")


@dataclasses.dataclass(eq=False)
class MariaDBCheck(SQLCheck):
    def create(self) -> bool:
        statement = f"ALTER TABLE {self.table.fully_qualified_name} ADD CONSTRAINT {self.quoted_name} CHECK ({self.expression})"
        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        statement = f"ALTER TABLE {self.table.fully_qualified_name} DROP CONSTRAINT {self.quoted_name}"
        return self.table.database.context.execute(statement)

    def alter(self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass(eq=False)
class MariaDBColumn(SQLColumn):
    set: Optional[list[str]] = None
    is_unsigned: Optional[bool] = False
    is_zerofill: Optional[bool] = False
    comment: Optional[str] = None
    po: Optional[SQLColumn] = None
    after_index: Optional[int] = None

    def add(self) -> bool:
        statement = f"ALTER TABLE {self.table.fully_qualified_name} ADD COLUMN {MariaDBColumnBuilder(self)}"
        if self.after_index:
            if self.after_index == 0:
                statement += " FIRST"
            else:
                statement += f" AFTER {self.table.columns.get_value()[self.after_index - 1].quoted_name}"

        return self.table.database.context.execute(statement)

    def modify(self, current: Self, after: Optional[SQLColumn] = None):
        statement = f"ALTER TABLE {self.table.fully_qualified_name} MODIFY COLUMN {MariaDBColumnBuilder(current)}"
        if after is not None:
            if after.id == -1:
                statement += " FIRST"
            else:
                statement += f" AFTER {after.quoted_name}"

        self.table.database.context.execute(statement)

    def change(self, current: Self):
        statement = f"ALTER TABLE {self.table.fully_qualified_name} CHANGE {self.quoted_name} {MariaDBColumnBuilder(current)}"
        self.table.database.context.execute(statement)

    def rename(self, new_name: str) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE {self.table.fully_qualified_name} RENAME COLUMN {self.quoted_name} TO `{new_name}`")

    def drop(self) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE {self.table.fully_qualified_name} DROP COLUMN {self.quoted_name}")


@dataclasses.dataclass(eq=False)
class MariaDBIndex(SQLIndex):
    def create(self) -> bool:
        if self.type == MariaDBIndexType.PRIMARY:
            return self.table.database.context.execute(f"""ALTER TABLE {self.table.fully_qualified_name} ADD PRIMARY KEY ({", ".join(self.columns)})""")

        return self.table.database.context.execute(f"""ALTER TABLE {self.table.fully_qualified_name} ADD {self.type.name} {self.quoted_name} ({", ".join(self.columns)})""")

    def drop(self) -> bool:
        if self.type == MariaDBIndexType.PRIMARY:
            return self.table.database.context.execute(f"ALTER TABLE {self.table.fully_qualified_name} DROP PRIMARY KEY")

        return self.table.database.context.execute(f"DROP INDEX {self.quoted_name} ON {self.table.fully_qualified_name}")

    def modify(self, new: Self):
        self.drop()

        new.create()


@dataclasses.dataclass(eq=False)
class MariaDBForeignKey(SQLForeignKey):
    def create(self) -> bool:
        query = [
            f"ALTER TABLE {self.table.fully_qualified_name} ADD CONSTRAINT {self.quoted_name}",
            f"FOREIGN KEY({', '.join(self.columns)})",
            f"REFERENCES `{self.reference_table}`({', '.join(self.reference_columns)})",
        ]

        if self.on_delete:
            query.append(f"ON DELETE {self.on_delete}")

        if self.on_update:
            query.append(f"ON UPDATE {self.on_update}")

        return self.table.database.context.execute(" ".join(query))

    def drop(self) -> bool:
        return self.table.database.context.execute(f"""
            ALTER TABLE {self.table.fully_qualified_name}
            DROP FOREIGN KEY `{self.name}`
        """)

    def modify(self, new: Self):
        self.drop()

        new.create()


class MariaDBRecord(SQLRecord):

    def raw_insert_record(self) -> str:
        columns_values = {}

        for column in self.table.columns:
            if column.virtuality is not None:
                continue

            value = self.values.get(column.name)
            if value is not None and str(value).strip():
                if column.datatype.format:
                    value = column.datatype.format(value)

                columns_values[column.name] = str(value)
            # elif column. :

        if not columns_values:
            assert False, "No columns values"

        return f"""INSERT INTO {self.table.fully_qualified_name} ({', '.join(columns_values.keys())}) VALUES ({', '.join(columns_values.values())})"""

    def raw_update_record(self) -> Optional[str]:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        sql_select = f"SELECT * FROM {self.table.fully_qualified_name} WHERE {identifier_conditions}"
        self.table.database.context.execute(sql_select)

        if not (existing_record := self.table.database.context.fetchone()):
            logger.warning(f"Record not found for update: {identifier_columns}")
            assert False, "Record not found for update with identifier columns"

        changed_columns = []

        for col_name, new_value in self.values.items():
            column: SQLColumn = next((c for c in self.table.columns if c.name == col_name), None)
            existing_value = dict(existing_record).get(col_name)
            if (new_value or "") != (existing_value or ""):
                if new_value is None:
                    changed_columns.append(f"`{col_name}` = NULL")
                elif column.datatype.format:
                    changed_columns.append(f"`{col_name}` = {column.datatype.format(new_value)}")
                else:
                    changed_columns.append(f"`{col_name}` = {new_value}")

        if not changed_columns:
            return None

        set_clause = ", ".join(changed_columns)

        return f"UPDATE {self.table.fully_qualified_name} SET {set_clause} WHERE {identifier_conditions}"

    def raw_delete_record(self) -> str:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        return f"DELETE FROM {self.table.fully_qualified_name} WHERE {identifier_conditions}"

    # RECORDS
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


class MariaDBView(SQLView):
    def create(self) -> bool:
        self.database.context.set_database(self.database)
        return self.database.context.execute(f"CREATE VIEW {self.fully_qualified_name} AS {self.statement}")

    def drop(self) -> bool:
        self.database.context.set_database(self.database)
        return self.database.context.execute(f"DROP VIEW IF EXISTS {self.fully_qualified_name}")

    def alter(self) -> bool:
        self.database.context.set_database(self.database)
        return self.database.context.execute(f"CREATE OR REPLACE VIEW {self.fully_qualified_name} AS {self.statement}")


class MariaDBTrigger(SQLTrigger):
    def create(self) -> bool:
        return self.database.context.execute(f"CREATE TRIGGER {self.fully_qualified_name} {self.statement}")

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TRIGGER IF EXISTS {self.fully_qualified_name}")

    def alter(self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass(eq=False)
class MariaDBFunction(SQLFunction):
    parameters: str = ""
    returns: str = ""
    deterministic: bool = False
    statement: str = ""

    def create(self) -> bool:
        deterministic = "DETERMINISTIC" if self.deterministic else "NOT DETERMINISTIC"
        query = f"""
            CREATE FUNCTION {self.fully_qualified_name}({self.parameters})
            RETURNS {self.returns}
            {deterministic}
            BEGIN
                {self.statement};
            END
        """
        return self.database.context.execute(query)

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP FUNCTION IF EXISTS {self.fully_qualified_name}")

    def alter(self) -> bool:
        self.drop()
        return self.create()


@dataclasses.dataclass(eq=False)
class MariaDBProcedure(SQLProcedure):
    parameters: str = ""
    statement: str = ""

    @staticmethod
    def _render_body(statement: str) -> str:
        body = statement.strip()
        if body.endswith(";"):
            return body

        return f"{body};"

    def create(self) -> bool:
        body = self._render_body(self.statement)
        query = f"""
            CREATE PROCEDURE {self.fully_qualified_name}({self.parameters})
            BEGIN
                {body}
            END
        """
        self.database.context.set_database(self.database)
        return self.database.context.execute(query)

    def drop(self) -> bool:
        self.database.context.set_database(self.database)
        return self.database.context.execute(
            f"DROP PROCEDURE IF EXISTS {self.fully_qualified_name}"
        )

    def alter(self) -> bool:
        self.drop()
        return self.create()
