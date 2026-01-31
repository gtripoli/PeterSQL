from typing import List, Optional

from structures.engines.builder import AbstractColumnBuilder, AbstractIndexBuilder
from structures.engines.database import SQLColumn


class MySQLColumnBuilder(AbstractColumnBuilder):
    TEMPLATE = ["%(name)s", "%(datatype)s", "%(unsigned)s", "%(zerofill)s",
                "%(collate)s", "%(nullable)s", "%(default)s", "%(auto_increment)s",
                "%(unique)s", "%(primary_key)s", "%(comment)s", "%(check)s",
                # TODO: COLUMN_FORMAT {FIXED|DYNAMIC|DEFAULT} - STORAGE {DISK|MEMORY}]
                # "%(format)s","%(storage)s",
                "%(generated)s"]

    def __init__(self, column: SQLColumn, exclude: List[str] | None = None):
        super().__init__(column, exclude)

        self.parts.update({
            "check": self.check,
            "unsigned": self.unsigned,
            "zerofill": self.zerofill,
            "comment": self.comment,
            "generated": self.generated,
        })

    @property
    def auto_increment(self):
        return "AUTO_INCREMENT" if self.column.is_auto_increment else ""

    @property
    def check(self):
        return f"CHECK ({self.column.check})" if self.column.check else ""

    @property
    def unsigned(self):
        return "UNSIGNED" if self.column.is_unsigned else ""

    @property
    def zerofill(self):
        return "ZEROFILL" if self.column.is_zerofill else ""

    @property
    def comment(self):
        return f"COMMENT '{self.column.comment}'" if self.column.comment else ""

    @property
    def generated(self):
        return f"AS ({self.column.expression}) {self.column.virtuality}" if self.column.virtuality is not None else ""


class MySQLIndexBuilder(AbstractIndexBuilder):
    TEMPLATE = ["%(type)s", "%(name)s", "(%(columns)s)"]

    def __init__(self, index: 'MariaDBIndex', exclude: Optional[List[str]] = None):
        super().__init__(index, exclude)

    @property
    def type(self):
        if self.index.type.name == "PRIMARY":
            return "PRIMARY KEY"
        elif self.index.type.name == "UNIQUE INDEX":
            return "UNIQUE KEY"
        elif self.index.type.name == "INDEX":
            return "KEY"
        elif self.index.type.name in ["FULLTEXT", "SPATIAL"]:
            return f"{self.index.type.name} KEY"
        else:
            return f"{self.index.type.name} KEY"

    @property
    def name(self):
        if self.index.type.name == "PRIMARY":
            return ""
        return f"`{self.index.name}`" if self.index.name else ""
