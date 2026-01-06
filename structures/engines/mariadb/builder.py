from typing import Optional, List

from structures.engines.context import AbstractColumnBuilder


class MariaDBColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(unsigned)s", "%(zerofill)s",
                "%(collate)s", "%(nullable)s", "%(default)s", "%(auto_increment)s",
                "%(comment)s", "%(check)s",
                # TODO: COLUMN_FORMAT {FIXED|DYNAMIC|DEFAULT} - STORAGE {DISK|MEMORY}]
                # "%(format)s","%(storage)s",
                "%(generated)s"]

    def __init__(self, column: 'MariaDBColumn', exclude: Optional[List[str]] = None):
        super().__init__(column, exclude)

        self.parts.update({
            'check': self.check,
            'unsigned': self.unsigned,
            'zerofill': self.zerofill,
            'comment': self.comment,
            'generated': self.generated,
        })

    @property
    def auto_increment(self):
        return 'AUTO_INCREMENT' if self.column.is_auto_increment else ''

    @property
    def check(self):
        return f"CHECK ({self.column.check})" if self.column.check else ''

    @property
    def unsigned(self):
        return f"UNSIGNED" if self.column.is_unsigned else ''

    @property
    def zerofill(self):
        return f"ZEROFILL" if self.column.is_zerofill else ''

    @property
    def comment(self):
        return f"COMMENT '{self.column.comment}'" if self.column.comment else ''

    @property
    def generated(self):
        return f"AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality is not None else ''
