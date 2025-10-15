import dataclasses
from datetime import datetime

from typing import Optional, Callable, Literal, List, Any, Iterator, Self

import wx

from helpers.lazylist import LazyList
from models.structures.indextype import SQLIndexType
from models.structures.datatype import SQLDataType


@dataclasses.dataclass
class SQLDatabase:
    id: Optional[int]
    name: str

    tables: LazyList['SQLTable'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))

    get_tables_handler: Callable[[Self], List['SQLTable']] = dataclasses.field(default_factory=lambda: lambda database: list([]))

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

    columns: LazyList['SQLColumn'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))
    indexes: LazyList['SQLIndex'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))
    foreign_keys: LazyList['SQLForeignKey'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))

    get_columns_handler: Callable[[Self], List['SQLColumn']] = dataclasses.field(default_factory=lambda: lambda table: list([]))
    get_indexes_handler: Callable[[Self], List['SQLIndex']] = dataclasses.field(default_factory=lambda: lambda table: list([]))
    get_foreign_keys_handler: Callable[[Self], List['SQLForeignKey']] = dataclasses.field(default_factory=lambda: lambda table: list([]))

    comment: Optional[str] = None
    count_rows: Optional[int] = None

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
        self.indexes = LazyList(lambda: self.get_indexes_handler(self))
        self.columns = LazyList(lambda: self.get_columns_handler(self))
        self.foreign_keys = LazyList(lambda: self.get_foreign_keys_handler(self))

    def is_valid(self) -> bool:
        print("table is valid:", self.name != "", len(self.columns) > 0, {c.name: c.is_valid for c in self.columns})
        return all([self.name != "", len(self.columns) > 0, all([c.is_valid for c in self.columns])])

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, SQLTable):
            return True

        if any([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.default_factory is dataclasses.MISSING
        ]):
            return True

        if any([c1 != c2 for c1, c2 in zip(self.columns, other.columns)]):
            return True

        if any([i1 != i2 for i1, i2 in zip(self.indexes, other.indexes)]):
            return True

        return False


@dataclasses.dataclass
class SQLColumn:
    id: int
    name: str
    table: SQLTable
    datatype: SQLDataType
    # get_indexes_handler: Callable[[SQLTable], Iterator['SQLIndex']] = dataclasses.field(default_factory=lambda: lambda index: iter([]))
    is_nullable: bool = False
    extra: Optional[str] = None
    # key: Optional[str] = None
    comment: Optional[str] = None

    server_default: Optional[str] = None

    is_unsigned: bool = False
    is_zerofill: bool = False
    is_auto_increment: bool = False
    is_primary_key: bool = False

    set: Optional[List[str]] = None
    length: Optional[int] = None

    collation_name: Optional[str] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    datetime_precision: Optional[int] = None
    virtuality: Optional[Literal["VIRTUAL", "STORED"]] = None
    expression: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, SQLColumn):
            return False

        return all([
            getattr(self, field.name) == getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.default_factory is dataclasses.MISSING and field.type != SQLTable
        ])

    @property
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

    def get_definition(self) -> dict:
        datatype_str = str(self.datatype.name)

        if self.datatype.has_length:
            datatype_str += f"({self.length or self.datatype.default_length})"

        if self.datatype.has_precision:
            if self.datatype.has_scale:
                datatype_str += f"({self.numeric_precision or self.datatype.default_precision},{self.numeric_scale or self.datatype.default_scale})"
            else:
                datatype_str += f"({self.numeric_precision or self.datatype.default_precision})"

        if self.datatype.has_set:
            datatype_str += f"""('{"','".join(list(set(self.set or self.datatype.default_set)))}')"""

        result = {
            'name': f"`{self.name}`",
            'datatype': datatype_str,
            'nullable': 'NOT NULL' if not self.is_nullable else 'NULL',
        }

        if self.default and self.default != '':
            result['default'] = f"DEFAULT {self.default}"

        if self.collation_name:
            result['collation'] = f"COLLATE {self.collation_name}"

        if self.comment:
            result['comment'] = f"COMMENT '{self.comment}'"

        if self.virtuality and self.expression:
            result['virtual'] = f"AS ({self.expression}) {self.virtuality}"

        return result


@dataclasses.dataclass
class SQLIndex:
    id: int
    name: str
    type: SQLIndexType
    columns: List[str]
    condition: str = dataclasses.field(default_factory=str)
    expression: List[str] = dataclasses.field(default_factory=list)

    def __ne__(self, other):
        if not isinstance(other, SQLIndex):
            return True

        return any([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.default_factory is dataclasses.MISSING
        ])


@dataclasses.dataclass
class SQLForeignKey:
    id: int
    name: str
    columns: List[str]
    reference_table: str = dataclasses.field(default_factory=str)
    reference_columns: List[str] = dataclasses.field(default_factory=list)

    on_update: str = dataclasses.field(default_factory=str)
    on_delete: str = dataclasses.field(default_factory=str)

    def __eq__(self, other):
        if not isinstance(other, SQLForeignKey):
            return False

        return all([
            getattr(self, field.name) == getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.default_factory is dataclasses.MISSING
        ])