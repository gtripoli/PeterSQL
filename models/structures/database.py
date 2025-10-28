import dataclasses
from datetime import datetime

from typing import Optional, Callable, Literal, List, Any, Self, Dict

import wx

from icons import BitmapList

from helpers.lazylist import LazyList
from models.structures.indextype import SQLIndexType
from models.structures.datatype import SQLDataType
from models.structures.sqlite.indextype import SQLiteIndexType


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

    # columns: LazyList['SQLColumn'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))
    # indexes: LazyList['SQLIndex'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))
    # foreign_keys: LazyList['SQLForeignKey'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))
    # records: LazyList['SQLRecord'] = dataclasses.field(default_factory=lambda: LazyList(lambda: list([])))

    get_columns_handler: Callable[[Self], List['SQLColumn']] = dataclasses.field(default_factory=lambda: lambda table: list([]))
    get_indexes_handler: Callable[[Self], List['SQLIndex']] = dataclasses.field(default_factory=lambda: lambda table: list([]))
    get_foreign_keys_handler: Callable[[Self], List['SQLForeignKey']] = dataclasses.field(default_factory=lambda: lambda table: list([]))
    get_records_handler: Callable[[Self, int, int], List['SQLRecord']] = dataclasses.field(default_factory=lambda: lambda table, limit=1000, offset=0: list([]))

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
        self.records = LazyList(lambda: self.get_records_handler(self))

    def is_valid(self) -> bool:
        print("table is valid:", self.name != "", len(self.columns) > 0, {c.name: c.is_valid for c in self.columns})
        return all([
            self.name != "",
            len(self.columns) > 0,
            all([c.is_valid for c in self.columns]),
            all([ix.is_valid for ix in self.indexes]),
            all([fk.is_valid for fk in self.foreign_keys]),
        ])

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

    def get_identifier_indexes(self) -> List['SQLIndex']:
        identifier_indexes = []
        for index in list(self.indexes):
            if index.type.is_primary or index.type.is_unique:
                identifier_indexes.append(index)

        return identifier_indexes


@dataclasses.dataclass
class SQLColumn:
    id: int
    name: str
    table: SQLTable
    datatype: SQLDataType
    is_nullable: bool = False
    extra: Optional[str] = None
    comment: Optional[str] = None

    server_default: Optional[str] = None

    is_unsigned: bool = False
    is_zerofill: bool = False
    is_auto_increment: bool = False

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
    def is_primary_key(self):
        if self.table:
            return any([i.type == SQLiteIndexType.PRIMARY for i in list(self.table.indexes) if self.name in i.columns])

        return False

    @property
    def is_valid(self):
        if not all([self.name, self.datatype]) :
            return False

        if self.datatype.has_length and not self.length:
            return False

        if self.datatype.has_precision and not self.numeric_precision:
            return False

        if self.datatype.has_scale and not self.numeric_scale:
            return False

        if self.datatype.has_set and not self.set:
            return False

        return True

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
            (self.datatype.has_precision, "numeric_precision", lambda value: [v.strip("'") for v in value.split(",")][0], self.datatype.default_precision),
            (self.datatype.has_scale, "numeric_scale", lambda value: [v.strip("'") for v in value.split(",")][1], self.datatype.default_scale),
            (self.datatype.has_set, "set", lambda value: [v.strip("'") for v in value.split(",")], self.datatype.default_set),
        ]

        for condition, attr, transform, default in candidates:
            if condition:
                setattr(self, attr, transform(value))
                break

    @property
    def default(self) -> str:
        default = ""

        if self.is_auto_increment:
            default = 'AUTO_INCREMENT'

        elif self.server_default is not None:
            default = self.server_default

            if self.extra is not None:
                default += ' ' + self.extra

        return default

    @default.setter
    def default(self, value):
        if value == 'AUTO_INCREMENT':
            self.is_auto_increment = True
            self.server_default = None
        else:
            self.server_default = value


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

    @property
    def is_valid(self):
        return all([self.name, self.type, len(self.columns)])


@dataclasses.dataclass
class SQLForeignKey:
    id: int
    name: str
    columns: List[str]
    reference_table: str
    reference_columns: List[str]

    on_update: str
    on_delete: str

    bitmap: wx.Bitmap = BitmapList.KEY_FOREIGN

    def __eq__(self, other):
        if not isinstance(other, SQLForeignKey):
            return False

        return all([
            getattr(self, field.name) == getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.default_factory is dataclasses.MISSING
        ])

    @property
    def is_valid(self):
        return all([self.name, len(self.columns), self.reference_table, len(self.reference_columns)])


class SQLRecord:
    def __init__(self, _id: int = -1, table: 'SQLTable' = None, **kwargs):
        self._id = _id
        self._table = table
        self._data: Dict[str, Any] = {}

        if table:
            for col in table.columns:
                value = kwargs.get(col.name)
                self._data[col.name] = value
        else:
            self._data.update(kwargs)

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.__setattr__(key, value)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def is_new(self) -> bool:
        return self._id == -1

    def is_valid(self) -> bool:
        for column in self._table.columns:
            value = self._data.get(column.name)

            if column.is_nullable:
                continue

            if column.datatype.name == "BOOLEAN":
                continue

            if value is None:
                if column.is_auto_increment or column.server_default:
                    continue

                return False

        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SQLRecord):
            return False

        return self._data == other._data
