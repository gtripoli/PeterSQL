from typing import Optional, List

from structures.engines.context import AbstractColumnBuilder, AbstractIndexBuilder


class PostgreSQLColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(collate)s", "%(nullable)s", "%(default)s", "%(check)s", "%(generated)s"]

    def __init__(self, column: 'PostgreSQLColumn', exclude: Optional[List[str]] = None):
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
    TEMPLATE = ["%(type)s", "%(name)s", "ON", "%(table)s", "(%(columns)s)"]

    def __init__(self, index: 'PostgreSQLIndex', exclude: Optional[List[str]] = None):
        super().__init__(index, exclude)

    @property
    def type(self):
        if self.index.type.name == "PRIMARY":
            return "ALTER TABLE ADD CONSTRAINT PRIMARY KEY"
        elif self.index.type.name == "UNIQUE INDEX":
            return "CREATE UNIQUE INDEX"
        else:
            return f"CREATE INDEX"

    @property
    def name(self):
        if self.index.type.name == "PRIMARY":
            return f'"{self.index.name}"'
        return f'"{self.index.name}"' if self.index.name else ''

    @property
    def table(self):
        return f'"{self.index.table.database.name}"."{self.index.table.name}"'

    @property
    def columns(self):
        return ", ".join(f'"{col}"' for col in self.index.columns)
