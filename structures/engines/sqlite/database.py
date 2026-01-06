import dataclasses
from typing import Self, List, Optional, Dict, Tuple

from helpers.logger import logger

from structures.engines import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase

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

    def create(self) -> bool:
        constraints = []
        primary_keys = []
        columns_definitions: Dict[str, str] = {}

        unique_indexes_multiple_columns = [index for index in self.indexes if index.type == SQLiteIndexType.UNIQUE and len(index.columns) > 1 and index.name.startswith('sqlite_autoindex_')]

        for current in self.columns.get_value():
            if current:
                if current.is_primary_key or current.is_auto_increment:
                    primary_keys.append(current)

                exclude = ['unique']

                if len(primary_keys) > 1:
                    exclude += ['primary_key', 'auto_increment']

                columns_definitions[current.name] = str(SQLiteColumnBuilder(current, exclude=exclude))

        for unique_index_multiple_columns in unique_indexes_multiple_columns:
            cols = ", ".join([f'`{c}`' for c in unique_index_multiple_columns.columns])

            constraints.append(f"UNIQUE ({cols})")

        # Handle primary keys
        if len(primary_keys) > 1:
            # Check if any autoincrement
            auto_increment = next((pk for pk in primary_keys if pk.is_auto_increment), None)
            if auto_increment:
                # If autoincrement and multiple primary keys, use UNIQUE
                cols = ", ".join([f'`{pk.name}`' for pk in primary_keys])
                constraints.append(f"UNIQUE ({cols})")
            else:
                columns_definitions = {col_name: col_def.replace(' PRIMARY KEY', '') for col_name, col_def in columns_definitions.items()}
                # Use PRIMARY KEY table constraint
                cols = ", ".join([f'`{pk.name}`' for pk in primary_keys])
                constraints.append(f"PRIMARY KEY ({cols})")

        # Handle foreign keys
        foreign_key_is_already_present = any(['FOREIGN KEY' in column_definition for column_definition in columns_definitions])

        if not foreign_key_is_already_present:
            for fk in self.foreign_keys:
                cols = ", ".join([f"`{c}`" for c in fk.columns])
                ref_cols = ", ".join([f"`{c}`" for c in fk.reference_columns])
                constraint = f"FOREIGN KEY ({cols}) REFERENCES {fk.reference_table} ({ref_cols})"
                if fk.on_update and fk.on_update != "NO ACTION":
                    constraint += f" ON UPDATE {fk.on_update}"
                if fk.on_delete and fk.on_delete != "NO ACTION":
                    constraint += f" ON DELETE {fk.on_delete}"
                constraints.append(constraint)

        sql = f"CREATE TABLE `{self.name}` ({', '.join(list(columns_definitions.values()) + constraints)})"

        return self.database.context.execute(sql)

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
            with self.database.context.transaction() as transaction:
                if original_table:
                    if self.name != original_table.name:
                        self.rename(original_table, self.name)
                    if self.auto_increment != original_table.auto_increment:
                        self.set_auto_increment(self.auto_increment)

                # SQLite does not support ALTER COLUMN or ADD CONSTRAINT,
                # so rename and recreate the table with the new columns and constraints
                if needs_recreate:
                    transaction.execute("PRAGMA foreign_keys = OFF")

                    temp_name = f"_{original_name}_{self.generate_uuid()}"

                    self.name = temp_name

                    self.create()

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

                    transaction.execute("PRAGMA foreign_keys = ON")

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

        return True

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TABLE `{self.name}`")


@dataclasses.dataclass(eq=False)
class SQLiteColumn(SQLColumn):
    def add(self) -> bool:
        sql = f"ALTER TABLE `{self.table.name}` ADD COLUMN {str(SQLiteColumnBuilder(self, exclude=['primary_key', 'auto_increment']))}"
        if  (after := getattr(self, "after", None)) is not None:
            sql += f" AFTER {after}"
            
        return self.table.database.context.execute(sql)

    def modify(self):
        new_name = f"_{self.table.name}_{self.generate_uuid()}"

        for i, c in enumerate(self.table.columns):
            if c.name == self.name:
                self.table.columns[i] = self
                break

        with self.table.database.context.transaction() as transaction:
            self.table.rename(self.table, new_name)

            self.table.create()

            transaction.execute(f"INSERT INTO `{self.table.name}` SELECT * FROM {new_name};")

            transaction.execute(f"DROP TABLE {new_name};")

    def rename(self, new_name: str) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE `{self.table.name}` RENAME COLUMN `{self.name}` TO `{new_name}`")

    def drop(self, table: SQLTable, column: SQLColumn) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE `{table.name}` DROP COLUMN `{self.name}`")

    # def recreate_table_for_foreign_keys(self):
    #     new_name = f"_{self.table.name}_{self.generate_uuid()}"
    #
    #     self.table.rename(new_name)
    #
    #     self.table.create()
    #
    #     cols = ", ".join([f"`{c.name}`" for c in self.table.columns])
    #     self.database.context.execute(f"INSERT INTO `{self.table.name}` ({cols}) SELECT {cols} FROM {new_name};")
    #
    #     # Drop old table
    #     self.database.context.execute(f"DROP TABLE {new_name};")
    #
    #     # Recreate non-primary indexes
    #     for index in self.table.indexes:
    #         if index.type != SQLiteIndexType.PRIMARY:
    #             index.create()


@dataclasses.dataclass(eq=False)
class SQLiteIndex(SQLIndex):
    def create(self) -> bool:
        if self.type == SQLiteIndexType.PRIMARY:
            return False  # PRIMARY is handled in table creation

        if self.type == SQLiteIndexType.UNIQUE and self.name.startswith("sqlite_autoindex_"):
            return False  # UNIQUE is handled in table creation

        unique_index = "UNIQUE INDEX" if self.type == SQLiteIndexType.UNIQUE else "INDEX"

        if self.type == SQLiteIndexType.EXPRESSION:
            expression = ", ".join(self.expression)
        else:
            expression = ", ".join(self.columns)

        where_str = f"WHERE {self.condition}" if self.condition else ""

        return self.table.database.context.execute(f"CREATE {unique_index} IF NOT EXISTS {self.name} ON {self.table.name}({expression}) {where_str}")

    def drop(self) -> bool:
        if self.type == SQLiteIndexType.PRIMARY:
            return False

        if self.type == SQLiteIndexType.UNIQUE and self.name.startswith("sqlite_autoindex_"):
            return False  # sqlite_ UNIQUE is handled in table creation

        return self.table.database.context.execute(f"DROP INDEX IF EXISTS {self.name}")

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

    def drop(self):
        return self.database.context.execute(f"DROP VIEW IF EXISTS {self.name}")

    def alter(self):
        pass


class SQLiteTrigger(SQLTrigger):
    def create(self) -> bool:
        return self.database.context.execute(f"CREATE TRIGGER IF NOT EXISTS {self.name} {self.sql}")

    def drop(self):
        return self.database.context.execute(f"DROP TRIGGER IF EXISTS {self.name}")

    def alter(self):
        pass
