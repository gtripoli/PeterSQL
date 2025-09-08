import datetime
import dataclasses

from typing import Optional, Callable, List, Type, Any, Dict, Literal

import wx
import sqlalchemy

from helpers.lazylist import LazyList
from models.structures import SQLDataType


@dataclasses.dataclass
class Index:
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


@dataclasses.dataclass
class Column:
    id: Optional[int]
    name: str
    datatype: SQLDataType
    is_nullable: bool
    extra: Optional[str] = None
    key: Optional[str] = None
    comment: Optional[str] = None

    server_default: Optional[str] = None

    is_unsigned: bool = False
    is_zerofill: bool = False
    is_auto_increment: bool = False

    set: Optional[List[str]] = None
    length: Optional[int] = None

    character_set: Optional[str] = None
    collation_name: Optional[str] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    datetime_precision: Optional[int] = None

    virtuality: Optional[Literal["VIRTUAL", "STORED"]] = None
    expression: Optional[str] = None

    indexes: List[Index] = dataclasses.field(default_factory=list)

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
            (self.datatype.has_set, "enums", lambda v: ",".join(v), self.datatype.default_set),
        ]

        length_scale_set = ""

        for condition, attr, transform, default in candidates:
            if condition:
                if value := getattr(self, attr, None):
                    length_scale_set = transform(value)
                else:
                    length_scale_set = transform(default)

                print("length_scale_set", length_scale_set)
                break

        if self.datatype.has_scale:
            if scale := getattr(self, "numeric_scale", None):
                length_scale_set += f",{scale}"
            else:
                length_scale_set += f",{self.datatype.default_scale}"

            print("length_scale_set scale", length_scale_set)

        return length_scale_set

    @length_scale_set.setter
    def length_scale_set(self, value):
        candidates = [
            (self.datatype.has_length, "length", str, self.datatype.default_length),
            (self.datatype.has_precision, "numeric_precision", str, self.datatype.default_precision),
            (self.datatype.has_set, "enums", lambda v: ",".join(v), self.datatype.default_set),
        ]

        for condition, attr, transform, default in candidates:
            if condition:
                setattr(self, attr, value)
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


@dataclasses.dataclass
class Table:
    id: int
    name: str
    schema: str

    engine: Optional[str]

    get_columns: Callable[[str, str], List[Column]]

    comment: Optional[str] = None
    count_rows: Optional[int] = None
    columns: List[Column] = dataclasses.field(default_factory=list)

    auto_increment: Optional[int] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    control: Optional[wx.Control] = None

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
        self.columns = LazyList(lambda: self.get_columns(self.schema, self.name))

    def is_valid(self) -> bool:
        return all([self.name != "", len(self.columns) > 0, all([c.is_valid for c in self.columns])])


@dataclasses.dataclass
class Database:
    id: Optional[int]
    name: str

    get_tables: Callable[[str], List[Table]]

    control: Optional[wx.Control] = None

    def __post_init__(self):
        self.tables = LazyList(lambda: self.get_tables(self.name))
