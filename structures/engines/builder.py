import abc
from typing import Optional

from helpers.logger import logger


class AbstractColumnBuilder(abc.ABC):
    TEMPLATE: str

    parts: dict[str, str]

    def __init__(self, column: 'SQLColumn', exclude: Optional[list[str]] = None):
        self.column = column
        self.exclude = exclude

        self.parts = {
            'name': self.name,
            'datatype': self.datatype,
            'unique': self.unique,
            'auto_increment': self.auto_increment,
            'nullable': self.nullable,
            'default': self.default,
            'collate': self.collate
        }

    @property
    def name(self):
        return self.column.sql_safe_name

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
            datatype_str += f"({self.column.set or self.column.datatype.default_set})"

        return datatype_str

    @property
    def auto_increment(self):
        raise Exception("the auto increment should be defined in the engine column's table builder")

    @property
    def nullable(self):
        return 'NOT NULL' if any([not self.column.is_nullable, self.column.is_primary_key, self.column.is_auto_increment]) else 'NULL'

    @property
    def default(self):
        return f"DEFAULT {self.column.server_default}" if self.column.server_default and self.column.server_default != '' else ''

    @property
    def collate(self):
        return f"CHARSET SET {self.column.table.database.context.COLLATION[self.column.collation_name]} COLLATE {self.column.collation_name}" if self.column.collation_name else ''

    @property
    def virtual(self):
        return f"GENERATED ALWAYS AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality and self.column.expression else ''

    @property
    def unique(self):
        return 'UNIQUE' if self.column.is_unique_key else ''

    # @property
    # def references(self):
    #     return f"REFERENCES {self.column.references}" if self.column.references else ''

    def __str__(self) -> str:
        formatted_parts = []
        for template_part in self.TEMPLATE:
            if self.exclude and any(part in template_part for part in self.exclude):
                continue
            try:
                formatted = template_part % self.parts
            except Exception as ex:
                logger.error(ex, exc_info=True)

            if formatted_strip := formatted.strip():  # Only include non-empty parts
                formatted_parts.append(formatted_strip)

        return " ".join(formatted_parts)


class AbstractIndexBuilder(abc.ABC):
    TEMPLATE: list[str]

    parts: dict[str, str]

    def __init__(self, index: 'SQLIndex', exclude: Optional[list[str]] = None):
        self.index = index
        self.exclude = exclude

        self.parts = {
            'type': self.type,
            'name': self.name,
            'columns': self.columns,
        }

    @property
    def type(self):
        return str(self.index.type)

    @property
    def name(self):
        if self.index.name and self.index.name != "PRIMARY KEY":
            return self.index.sql_safe_name
        return ""

    @property
    def columns(self):
        build_sql_safe_name = self.index.table.database.context.build_sql_safe_name
        return ", ".join([build_sql_safe_name(col) for col in self.index.columns])

    def __str__(self) -> str:
        formatted_parts = []
        for template_part in self.TEMPLATE:
            if self.exclude and any(part in template_part for part in self.exclude):
                continue
            try:
                formatted = template_part % self.parts
            except Exception as ex:
                logger.error(ex, exc_info=True)

            if formatted_strip := formatted.strip():  # Only include non-empty parts
                formatted_parts.append(formatted_strip)

        return " ".join(formatted_parts)
