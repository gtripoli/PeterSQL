from engines.structures.context import AbstractColumnBuilder
from engines.structures.sqlite.database import SQLiteColumn


class SQLiteColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(primary_key)s", "%(auto_increment)s", "%(nullable)s", "%(unique)s", "%(check)s", "%(default)s", "%(collate)s", "%(generated)s", "%(references)s"]

    def __init__(self, column: SQLiteColumn):
        super().__init__(column)

        self.parts.update({
            'check': self.check,
            'generated': self.generated,
        })

    @property
    def primary_key(self):
        return 'PRIMARY KEY' if self.column.is_primary_key or self.column.is_auto_increment else ''

    @property
    def auto_increment(self):
        return 'AUTOINCREMENT' if self.column.is_auto_increment else ''

    @property
    def check(self):
        return f"CHECK ({self.column.check})" if self.column.check else ''

    @property
    def generated(self):
        return f"GENERATED ALWAYS AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality is not None else ''

