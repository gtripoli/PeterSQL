import dataclasses
from typing import Self, List, Optional, Dict, Tuple

from helpers.logger import logger

from structures.engines import merge_original_current
from structures.engines.context import QUERY_LOGS
from structures.engines.database import SQLTable, SQLColumn, SQLIndex, SQLForeignKey, SQLRecord, SQLView, SQLTrigger, SQLDatabase

from structures.engines.mariadb.indextype import MariaDBIndexType
from structures.engines.mariadb.builder import MariaDBColumnBuilder


@dataclasses.dataclass
class MariaDBDatabase(SQLDatabase):
    default_collation: str = None


@dataclasses.dataclass(eq=False)
class MariaDBTable(SQLTable):
    def alter_auto_increment(self, auto_increment: int):
        sql = f"ALTER TABLE `{self.database.name}`.`{self.name}` AUTO_INCREMENT {auto_increment};"
        self.database.context.execute(sql)

        return True

    def alter_collation(self, collation_name, convert: bool = True):
        charset = ""
        if convert:
            charset = f"CONVERT TO CHARACTER SET {self.database.context.COLLATIONS[collation_name]}"
        return self.database.context.execute(f"""ALTER TABLE `{self.database.name}`.`{self.name}` {charset} COLLATE {collation_name};""")

    def alter_engine(self, engine: str):
        sql = f"ALTER TABLE `{self.database.name}`.`{self.name}` ENGINE {engine};"
        self.database.context.execute(sql)

        return True

    def rename(self, table: Self, new_name: str) -> bool:
        sql = f"ALTER TABLE `{self.database.name}`.`{table.name}` RENAME TO `{new_name}`;"
        self.database.context.execute(sql)

        return True

    def truncate(self):
        try:
            with self.database.context.transaction() as context:
                context.execute(f"TRUNCATE TABLE `{self.database.name}`.`{self.name}`;")

        except Exception as ex:
            logger.error(ex, exc_info=True)

        return True

    def create(self) -> bool:
        with self.database.context.transaction() as transaction:
            sql = f"CREATE TABLE `{self.database.name}`.`{self.name}` ({', '.join([str(MariaDBColumnBuilder(column)) for column in self.columns])})"
            self.database.context.execute(sql)

            for index in self.indexes:
                index.create()

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

                for original, current in map_columns:
                    if original is None:
                        current.add()
                    elif current is None:
                        original.drop()
                    elif current.name != original.name:
                        original.rename(current.name)
                    elif current != original:
                        original.modify(current)

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
            logger.error(ex)
            raise

        return True

    def drop(self) -> bool:
        return self.database.context.execute(f"DROP TABLE `{self.database.name}`.`{self.name}`")


@dataclasses.dataclass(eq=False)
class MariaDBColumn(SQLColumn):
    set: Optional[List[str]] = None
    is_unsigned: Optional[bool] = False
    is_zerofill: Optional[bool] = False
    comment: Optional[str] = None
    after: Optional[str] = None

    def add(self) -> bool:
        sql = f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` ADD COLUMN {MariaDBColumnBuilder(self)}"
        if hasattr(self, 'after') and self.after:
            sql += f" AFTER `{self.after}`"

        return self.table.database.context.execute(sql)

    def modify(self, current: Self):
        sql = f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` MODIFY COLUMN {MariaDBColumnBuilder(current)}"
        self.table.database.context.execute(sql)

    def rename(self, new_name: str) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` RENAME COLUMN `{self.name}` TO `{new_name}`")

    def drop(self) -> bool:
        return self.table.database.context.execute(f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` DROP COLUMN `{self.name}`")


@dataclasses.dataclass(eq=False)
class MariaDBIndex(SQLIndex):
    def create(self) -> bool:
        if self.type == MariaDBIndexType.PRIMARY:
            return self.table.database.context.execute(f"""ALTER TABLE `{self.table.database.name}`.`{self.table.name}` ADD PRIMARY KEY ({", ".join(self.columns)})""")

        return self.table.database.context.execute(f"""ALTER TABLE `{self.table.database.name}`.`{self.table.name}` ADD {self.type.name} `{self.name}` ({", ".join(self.columns)})""")

    def drop(self) -> bool:
        if self.type == MariaDBIndexType.PRIMARY:
            return self.table.database.context.execute(f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` DROP PRIMARY KEY")

        return self.table.database.context.execute(f"DROP INDEX IF EXISTS {self.name} ON `{self.table.database.name}`.`{self.table.name}`")

    def modify(self, new: Self):
        self.drop()

        new.create()


@dataclasses.dataclass(eq=False)
class MariaDBForeignKey(SQLForeignKey):
    def create(self) -> bool:
        query = [
            f"ALTER TABLE `{self.table.database.name}`.`{self.table.name}` ADD CONSTRAINT `{self.name}`",
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
            ALTER TABLE `{self.table.database.name}`.`{self.table.name}`
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

        return f"""INSERT INTO `{self.table.database.name}`.`{self.table.name}` ({', '.join(columns_values.keys())}) VALUES ({', '.join(columns_values.values())})"""

    def raw_update_record(self) -> Optional[str]:
        identifier_columns = self._get_identifier_columns()

        identifier_conditions = " AND ".join([f"""`{identifier_name}` = {identifier_value}""" for identifier_name, identifier_value in identifier_columns.items()])

        sql_select = f"SELECT * FROM `{self.table.database.name}`.`{self.table.name}` WHERE {identifier_conditions}"
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

        return f"DELETE FROM `{self.table.database.name}`.`{self.table.name}` WHERE {identifier_conditions}"

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
        return self.database.context.execute(f"CREATE VIEW IF NOT EXISTS `{self.name}` AS {self.sql}")

    def drop(self):
        return self.database.context.execute(f"DROP VIEW IF EXISTS `{self.name}`")

    def alter(self):
        pass


class MariaDBTrigger(SQLTrigger):
    def create(self) -> bool:
        return self.database.context.execute(f"CREATE TRIGGER IF NOT EXISTS `{self.name}` {self.sql}")

    def drop(self):
        return self.database.context.execute(f"DROP TRIGGER IF EXISTS `{self.name}`")

    def alter(self):
        pass
