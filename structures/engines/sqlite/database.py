import dataclasses
from typing import Self, Optional, Dict

from helpers.logger import logger

from structures.helpers import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase, SQLCheck

from structures.engines.sqlite.builder import SQLiteColumnBuilder

from structures.engines.sqlite.indextype import SQLiteIndexType


@dataclasses.dataclass
class SQLiteDatabase(SQLDatabase):
    pass


@dataclasses.dataclass(eq=False)
class SQLiteTable(SQLTable):
    def set_auto_increment(self, auto_increment):
        sql = f"UPDATE sqlite_sequence SET seq = {auto_increment} WHERE name = '{self.name}';"
        self.database.context.execute(sql)

        return True

    def rename(self, table: Self, new_name: str) -> bool:
        sql = f"ALTER TABLE `{table.name}` RENAME TO `{new_name}`;"
        self.database.context.execute(sql)

        return True

    def truncate(self):
        try:
            with self.database.context.transaction() as context:
                context.execute(f"DELETE FROM `{self.name}`;")

                context.execute(f"DELETE FROM sqlite_sequence WHERE name='{self.name}';")

        except Exception as ex:
            logger.error(ex, exc_info=True)

        return True

    def raw_create(self) -> str:
        # PeterSQL schema emission policy (SQLite):
        #
        # - PRIMARY KEY
        #   * Single-column PRIMARY KEY is emitted inline in the column definition.
        #   * Multi-column PRIMARY KEY is always emitted as a table-level constraint.
        #   This mirrors SQLite requirements and preserves rowid / AUTOINCREMENT semantics.
        #
        # - UNIQUE
        #   * All UNIQUE constraints (single or multi-column) are emitted as explicit
        #     CREATE UNIQUE INDEX statements.
        #   * UNIQUE is never emitted inline nor as a table-level constraint.
        #   This avoids sqlite_autoindex_* artifacts, guarantees stable naming,
        #   and ensures reproducible schemas.
        #
        # - FOREIGN KEY
        #   * All FOREIGN KEY constraints are always emitted as table-level constraints.
        #   * Inline foreign keys are not used.
        #   * ON UPDATE / ON DELETE clauses are emitted only when different from
        #     SQLite defaults (NO ACTION).
        #   This ensures named constraints, support for composite keys,
        #   and reliable schema reconstruction.
        #
        # - CHECK
        #   * CHECK constraints are preserved and re-emitted exactly as defined.
        #   * Inline CHECK clauses are preferred when originally defined on a column;
        #     table-level CHECK constraints are emitted when the original scope
        #     is table-level.
        #   CHECK constraints do not generate sqlite_autoindex objects and can be
        #   safely round-tripped.
        #
        # - sqlite_autoindex_*
        #   * sqlite_autoindex_* objects are not treated as schema elements.
        #   * They are interpreted as the physical manifestation of PRIMARY KEY
        #     or UNIQUE constraints defined in the original table.
        #   * When rebuilding a table, PeterSQL reconstructs the logical constraints
        #     (PRIMARY KEY / UNIQUE) rather than recreating sqlite_autoindex_* objects
        #     directly.
        #
        # This strategy keeps the DDL explicit, deterministic, lossless,
        # and fully reproducible, while remaining aligned with SQLite internal behavior.

        constraints = []
        primary_keys = []
        unique_indexes = []
        columns_definitions: Dict[str, str] = {}

        for index in self.indexes:
            if index.type == SQLiteIndexType.PRIMARY:
                primary_keys.extend(index.columns)

            if index.type == SQLiteIndexType.UNIQUE:
                unique_indexes.append(index.columns)

                if index.name.startswith("sqlite_autoindex_"):
                    constraints.append(f"UNIQUE ({', '.join([f'`{col}`' for col in index.columns])})")

        for column in self.columns.get_value():
            exclude = ["references"]

            if column.is_primary_key and len(primary_keys) > 1:
                exclude.extend(['primary_key', 'auto_increment'])

            if column.is_unique_key and all([len(columns) > 1 for columns in unique_indexes if column.name in columns]):
                exclude.append("unique")

            columns_definitions[column.name] = str(SQLiteColumnBuilder(column, exclude=exclude))

        # Handle primary keys
        if len(primary_keys) > 1:
            constraints.append(f"CONSTRAINT pk_{self.name} PRIMARY KEY ({', '.join([f'`{pk}`' for pk in primary_keys])})")

        for check in self.checks:
            constraint = []
            if check.name:
                constraint.append(f"CONSTRAINT {check.name}")

            constraint.append(f"CHECK ({check.expression})")

            constraints.append(" ".join(constraint))

        for fk in self.foreign_keys:
            cols = ", ".join([f"`{c}`" for c in fk.columns])
            ref_cols = ", ".join([f"`{c}`" for c in fk.reference_columns])
            constraint = [
                f"CONSTRAINT `{fk.name}`",
                f"FOREIGN KEY ({cols})",
                f"REFERENCES `{fk.reference_table}` ({ref_cols})"
            ]
            if fk.on_update and fk.on_update != "NO ACTION":
                constraint.append(f"ON UPDATE {fk.on_update}")

            if fk.on_delete and fk.on_delete != "NO ACTION":
                constraint.append(f"ON DELETE {fk.on_delete}")

            constraints.append(" ".join(constraint))

        return f"CREATE TABLE `{self.name}` ({', '.join(list(columns_definitions.values()) + constraints)})"

    def create(self) -> bool:
        try:
            with self.database.context.transaction() as transaction:
                transaction.execute(self.raw_create())

                for index in self.indexes:
                    index.create()


        except Exception as ex:
            QUERY_LOGS.append(f"/* alter_table exception: {ex} */")
            logger.error(ex, exc_info=True)
            return False

        return True

    def alter(self) -> bool:
        original_table = next((t for t in self.database.tables if t.id == self.id), None)
        original_columns = list(original_table.columns)
        original_indexes = list(original_table.indexes)
        original_primary_keys = next((pk for pk in original_indexes if pk.type == SQLiteIndexType.PRIMARY), None)
        original_foreign_keys = list(original_table.foreign_keys)

        current_columns = list(self.columns)
        current_indexes = list(self.indexes)
        current_primary_keys = next((pk for pk in current_indexes if pk.type == SQLiteIndexType.PRIMARY), None)
        current_foreign_keys = list(self.foreign_keys)

        map_columns = merge_original_current(original_columns, current_columns)
        map_indexes = merge_original_current(original_indexes, current_indexes)

        original_name = self.name
        needs_recreate = False

        # Check for columns changes
        if any([
            original_columns != current_columns,
            original_primary_keys != current_primary_keys,
            original_foreign_keys != current_foreign_keys
        ]):
            needs_recreate = True

        try:
            self.database.context.execute("PRAGMA foreign_keys = OFF")

            with self.database.context.transaction() as transaction:
                if original_table:
                    if self.name != original_table.name:
                        self.rename(original_table, self.name)
                    if self.auto_increment != original_table.auto_increment:
                        self.set_auto_increment(self.auto_increment)

                # SQLite does not support ALTER COLUMN or ADD CONSTRAINT,
                # so rename and recreate the table with the new columns and constraints
                if needs_recreate:

                    temp_name = f"_{original_name}_{self.generate_uuid()}"

                    self.name = temp_name

                    transaction.execute(self.raw_create())

                    columns = []

                    for original, current in map_columns:
                        if current and current.virtuality is None:
                            if original is None:
                                if current.server_default is None:
                                    columns.append(f"""{None if current.is_nullable else "''"} as `{current.name}`""")
                                else:
                                    columns.append(f"""{current.server_default} as `{current.name}`""")
                            else:
                                if current.name == original.name:
                                    columns.append(f"{current.name}")
                                else:
                                    columns.append(f"{original.name} as `{current.name}`")

                    transaction.execute(f"INSERT INTO `{self.name}` SELECT {', '.join(columns)} FROM `{original_name}`;")

                    transaction.execute(f"DROP TABLE `{original_name}`;")

                    self.rename(self, original_name)

                    self.name = original_name

                    map_indexes = merge_original_current([], current_indexes)

                else:
                    # Perform supported ALTER operations
                    for original, current in map_columns:
                        if original is None:
                            current.add()

                        elif current is None:
                            original.drop()

                        elif current.name != original.name:
                            original.rename(current.name)

                        elif current != original:
                            original.modify(current)

                # INDEX
                for original_index, current_index in map_indexes:
                    if current_index is None:
                        original_index.drop()
                    elif original_index is None:
                        current_index.create()
                    elif original_index != current_index:
                        original_index.modify(current_index)

        except Exception as ex:
            QUERY_LOGS.append(f"/* alter_table exception: {ex} */")
            logger.error(ex, exc_info=True)
            return False

        finally:
            self.database.context.execute("PRAGMA foreign_keys = ON")

        return True

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TABLE `{self.name}`")


@dataclasses.dataclass(eq=False)
class SQLiteCheck(SQLCheck):
    # name: Optional[str] = None
    pass


@dataclasses.dataclass(eq=False)
class SQLiteColumn(SQLColumn):
    def add(self) -> bool:
        sql = f"ALTER TABLE {self.table.sql_safe_name} ADD COLUMN {str(SQLiteColumnBuilder(self, exclude=['primary_key', 'auto_increment']))}"

        return self.table.database.context.execute(sql)

    def rename(self, new_name: str) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE {self.table.sql_safe_name} RENAME COLUMN {self.sql_safe_name} TO `{new_name}`")

    def modify(self):
        sql_safe_new_name = self.table.database.context.build_sql_safe_name(f"_{self.table.name}_{self.generate_uuid()}")

        for i, c in enumerate(self.table.columns):
            if c.name == self.name:
                self.table.columns[i] = self
                break

        with self.table.database.context.transaction() as transaction:
            self.table.rename(self.table, sql_safe_new_name)

            self.table.create()

            transaction.execute(f"INSERT INTO {self.table.sql_safe_name} SELECT * FROM {sql_safe_new_name};")

            transaction.execute(f"DROP TABLE {sql_safe_new_name};")

    def drop(self, table: SQLTable, column: SQLColumn) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE {table.sql_safe_name} DROP COLUMN {self.sql_safe_name}")


@dataclasses.dataclass(eq=False)
class SQLiteIndex(SQLIndex):
    def create(self) -> bool:
        if self.type == SQLiteIndexType.PRIMARY:
            return False  # PRIMARY is handled in table creation

        if self.type == SQLiteIndexType.UNIQUE and self.name.startswith("sqlite_autoindex_"):
            return False  # CONSTRAINT UNIQUE is handled in table creation

        unique_index = "UNIQUE INDEX" if self.type == SQLiteIndexType.UNIQUE else "INDEX"

        build_sql_safe_name = self.table.database.context.build_sql_safe_name

        columns_clause = ", ".join([build_sql_safe_name(column) for column in self.columns])
        where_clause = f" WHERE {self.condition}" if self.condition else ""

        statement = (
            f"CREATE {unique_index} IF NOT EXISTS {self.sql_safe_name} "
            f"ON {self.table.sql_safe_name}({columns_clause}){where_clause} "
        )

        return self.table.database.context.execute(statement)

    def drop(self) -> bool:
        if self.type == SQLiteIndexType.PRIMARY:
            return False

        if self.type == SQLiteIndexType.UNIQUE and self.name.startswith("sqlite_autoindex_"):
            return False  # sqlite_ UNIQUE is handled in table creation

        return self.table.database.context.execute(
            f"DROP INDEX IF EXISTS {self.sql_safe_name}"
        )

    def modify(self, new_index: Self):
        self.drop()

        new_index.create()


@dataclasses.dataclass(eq=False)
class SQLiteForeignKey(SQLForeignKey):
    pass


class SQLiteRecord(SQLRecord):
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

        return f"""INSERT INTO `{self.table.name}` ({', '.join(columns_values.keys())}) VALUES ({', '.join(columns_values.values())})"""

    def raw_update_record(self) -> Optional[str]:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        sql_select = f"SELECT * FROM `{self.table.name}` WHERE {identifier_conditions}"
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

        return f"UPDATE `{self.table.database.name}`.`{self.table.name}` SET {set_clause} WHERE {identifier_conditions}"

    def raw_delete_record(self) -> str:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        return f"DELETE FROM `{self.table.name}` WHERE {identifier_conditions}"

    def insert(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_insert_record := self.raw_insert_record():
                try:
                    return transaction.execute(raw_insert_record)
                except:
                    return False

        return False

    def update(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_update_record := self.raw_update_record():
                try:
                    return transaction.execute(raw_update_record)
                except:
                    return False

            return False

    def delete(self) -> bool:
        with self.table.database.context.transaction() as transaction:
            if raw_delete_record := self.raw_delete_record():
                try:
                    return transaction.execute(raw_delete_record)
                except:
                    return False

        return False


class SQLiteView(SQLView):
    def create(self) -> bool:
        return self.database.context.execute(f"CREATE VIEW IF NOT EXISTS {self.name} AS {self.sql}")

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP VIEW IF EXISTS {self.name}")

    def alter(self) -> bool:
        self.drop()
        return self.create()


class SQLiteTrigger(SQLTrigger):
    def create(self) -> bool:
        return self.database.context.execute(f"CREATE TRIGGER IF NOT EXISTS {self.name} {self.sql}")

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TRIGGER IF EXISTS {self.name}")

    def alter(self) -> bool:
        self.drop()
        return self.create()
