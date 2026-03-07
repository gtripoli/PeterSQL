from typing import Optional

from structures.engines.builder import AbstractColumnBuilder, AbstractIndexBuilder


class PostgreSQLColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(collate)s", "%(nullable)s", "%(default)s", "%(check)s", "%(generated)s"]

    def __init__(self, column: 'PostgreSQLColumn', exclude: Optional[list[str]] = None):
        super().__init__(column, exclude)

        self.parts.update({
            'check': self.check,
            'generated': self.generated,
        })

    @property
    def name(self):
        return f'"{self.column.name}"'

    @property
    def auto_increment(self):
        return "SERIAL" if self.column.datatype.name == "INTEGER" else ""

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

        return datatype_str

    @property
    def nullable(self):
        return 'NOT NULL' if not self.column.is_nullable else ''

    @property
    def default(self):
        return f"DEFAULT {self.column.server_default}" if self.column.server_default and self.column.server_default != '' else ''

    @property
    def collate(self):
        return f"COLLATE {self.column.collation_name}" if self.column.collation_name else ''

    @property
    def check(self):
        return f"CHECK ({self.column.check})" if self.column.check else ''

    @property
    def generated(self):
        if self.column.virtuality and self.column.expression:
            return f"GENERATED ALWAYS AS ({self.column.expression}) {self.column.virtuality.upper()}"
        return ''


class PostgreSQLIndexBuilder(AbstractIndexBuilder):
    # Different templates for inline (CREATE TABLE) vs standalone (CREATE INDEX)
    INLINE_TEMPLATE = ["%(type)s", "(%(columns)s)"]  # For PRIMARY KEY inside CREATE TABLE
    STANDALONE_TEMPLATE = ["%(type)s", "%(name)s", "ON", "%(table)s", "(%(columns)s)"]  # For CREATE INDEX

    def __init__(self, index: 'PostgreSQLIndex', exclude: Optional[list[str]] = None, inline: bool = False):
        self.inline = inline  # True when building for CREATE TABLE, False for standalone CREATE INDEX
        super().__init__(index, exclude)
        
        # Use appropriate template based on context
        if self.inline and self.index.type.name == "PRIMARY":
            self.TEMPLATE = self.INLINE_TEMPLATE
        else:
            self.TEMPLATE = self.STANDALONE_TEMPLATE
        
        # Add table to parts dictionary for standalone template
        self.parts['table'] = self.table

    @property
    def type(self):
        if self.index.type.name == "PRIMARY":
            return "PRIMARY KEY" if self.inline else "ALTER TABLE ADD CONSTRAINT PRIMARY KEY"
        elif self.index.type.name == "UNIQUE INDEX":
            return "UNIQUE" if self.inline else "CREATE UNIQUE INDEX"
        else:
            return f"CREATE INDEX"

    @property
    def name(self):
        if self.index.type.name == "PRIMARY":
            return f'"{self.index.name}"' if not self.inline else ''
        return f'"{self.index.name}"' if self.index.name else ''

    @property
    def table(self):
        # Use schema if available, otherwise use database name
        schema_or_db = self.index.table.schema if hasattr(self.index.table, 'schema') and self.index.table.schema else self.index.table.database.name
        return f'"{schema_or_db}"."{self.index.table.name}"'

    @property
    def columns(self):
        return ", ".join(f'"{col}"' for col in self.index.columns)
