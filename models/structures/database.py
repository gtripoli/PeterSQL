import dataclasses
from datetime import datetime

from typing import Optional, Callable, Literal, List, Any, Iterator, Self

import wx

from helpers.lazylist import LazyList
from models.structures.datatype import SQLDataType


@dataclasses.dataclass
class SQLDatabase:
    id: Optional[int]
    name: str

    get_tables_handler: Callable[[Self], Iterator['SQLTable']]

    control: Optional[wx.Control] = None

    def __post_init__(self):
        self.tables = LazyList(lambda: self.get_tables_handler(self))

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, SQLDatabase):
            return True

        if any([field != getattr(other, field.name) for field in dataclasses.fields(self)]):
            return True

        return any([t1 != t2 for t1, t2 in zip(self.tables, other.tables)])


@dataclasses.dataclass
class SQLTable:
    id: int
    name: str

    database: SQLDatabase
    engine: Optional[str]

    get_columns_handler: Callable[[SQLDatabase, Self], Iterator['SQLColumn']]

    comment: Optional[str] = None
    count_rows: Optional[int] = None
    columns: LazyList['SQLColumn'] = dataclasses.field(default_factory=lambda: LazyList(lambda: iter([])))

    auto_increment: Optional[int] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    control: Optional[wx.Control] = None
    collation_name: Optional[str] = None

    row_format: Optional[str] = None
    table_rows: Optional[int] = None
    avg_row_length: Optional[int] = None
    data_length: Optional[int] = None
    max_data_length: Optional[int] = None
    index_length: Optional[int] = None
    data_free: Optional[int] = None
    check_time: Optional[datetime] = None
    table_collation: Optional[str] = None
    checksum: Optional[int] = None
    create_options: Optional[str] = None
    max_index_length: Optional[int] = None
    temporary: bool = False

    def __post_init__(self):
        self.columns = LazyList(lambda: self.get_columns_handler(self.database, self))

    def is_valid(self) -> bool:
        return all([self.name != "", len(self.columns) > 0, all([c.is_valid for c in self.columns])])

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, SQLTable):
            return True

        if any([field != getattr(other, field.name) for field in dataclasses.fields(self)]):
            return True

        return any([c1 != c2 for c1, c2 in zip(self.columns, other.columns)])


@dataclasses.dataclass
class SQLColumn:
    id: Optional[int]
    name: str
    datatype: SQLDataType
    is_nullable: Optional[bool] = False
    extra: Optional[str] = None
    key: Optional[str] = None
    comment: Optional[str] = None

    server_default: Optional[str] = None

    is_unsigned: bool = False
    is_zerofill: bool = False
    is_auto_increment: bool = False

    set: Optional[List[str]] = None
    length: Optional[int] = None

    # character_set: Optional[str] = None
    collation_name: Optional[str] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    datetime_precision: Optional[int] = None

    virtuality: Optional[Literal["VIRTUAL", "STORED"]] = None
    expression: Optional[str] = None

    indexes: List['SQLIndex'] = dataclasses.field(default_factory=list)

    def __sub__(self, other):
        return {
            field: (getattr(self, field), getattr(other, field))
            for field in dataclasses.fields(self)
            if getattr(self, field) != getattr(other, field)
        }

    @property
    def is_primary(self) -> bool:
        return any(index.is_primary for index in self.indexes)

    def is_valid(self):
        return all([self.name, self.datatype])

    @property
    def length_scale_set(self) -> str:
        candidates = [
            (self.datatype.has_length, "length", str, self.datatype.default_length),
            (self.datatype.has_precision, "numeric_precision", str, self.datatype.default_precision),
            (self.datatype.has_set, "set", lambda v: ",".join(v), self.datatype.default_set),
        ]

        length_scale_set = ""

        for condition, attr, transform, default in candidates:
            if condition:
                if value := getattr(self, attr, None):
                    length_scale_set = transform(value)  # type: ignore[operator]
                else:
                    length_scale_set = transform(default)  # type: ignore[operator]

                break

        if self.datatype.has_scale:
            if scale := getattr(self, "numeric_scale", None):
                length_scale_set += f",{scale}"
            else:
                length_scale_set += f",{self.datatype.default_scale}"

        return length_scale_set

    @length_scale_set.setter
    def length_scale_set(self, value):
        candidates = [
            (self.datatype.has_length, "length", str, self.datatype.default_length),
            (self.datatype.has_precision, "numeric_precision", str, self.datatype.default_precision),
            (self.datatype.has_set, "set", lambda value: [v.strip("'") for v in value.split(",")], self.datatype.default_set),
        ]

        for condition, attr, transform, default in candidates:
            if condition:
                setattr(self, attr, transform(value))
                break

        if self.datatype.has_scale:
            setattr(self, "numeric_scale", value)

    @property
    def default(self) -> str:
        default = ""

        if self.is_auto_increment is True:
            return "AUTO_INCREMENT"

        else:
            if self.server_default is not None:
                default = self.server_default

            if self.extra is not None:
                default += ' ' + self.extra

        return default

    @default.setter
    def default(self, value):
        if self.is_auto_increment:
            self.server_default = None
        else:
            self.server_default = value

    def to_sql(self):
        parts = [str(self.datatype)]

        if self.datatype.has_length:
            parts.append(f"({self.length or self.datatype.default_length})")

        if self.datatype.has_precision:
            if self.datatype.has_scale:
                parts.append(f"({self.numeric_precision or self.datatype.default_precision}, {self.numeric_scale or self.datatype.default_scale})")

            parts.append(f"({self.numeric_precision or self.datatype.default_precision})")

        if self.datatype.has_set:
            parts.append(f"({self.set or self.datatype.default_set})")

        if self.datatype.has_unsigned:
            parts.append("UNSIGNED")

        if not self.is_nullable:
            parts.append("NOT NULL")

        if self.default is not None:
            parts.append(f"DEFAULT {self.default}")

        if self.extra:
            parts.append(self.extra)

        if self.comment:
            parts.append(f"COMMENT '{self.comment}'")

        if self.collation_name:
            parts.append(f"COLLATE {self.collation_name}")

        return " ".join(parts)


@dataclasses.dataclass
class SQLIndex():
    name: str
    type: str
    columns: List[str]
    is_primary: bool = False
    is_unique: bool = False
    is_fulltext: bool = False
    is_spatial: bool = False

    @property
    def is_normal(self):
        return not any([self.is_primary, self.is_unique, self.is_fulltext, self.is_spatial])
