import abc
import dataclasses
import uuid
from datetime import datetime

from typing import Optional, Callable, Literal, List, Any, Self, Dict

import wx

from helpers.lazylist import LazyList
from helpers.observables import ObservableList
from icons import BitmapList

from engines.structures.indextype import SQLIndexType
from engines.structures.datatype import SQLDataType
from engines.structures.sqlite.indextype import SQLiteIndexType


@dataclasses.dataclass
class SQLDatabase:
    id: Optional[int]
    name: str
    context: 'AbstractContext'

    get_tables_handler: Callable[[Self], List['SQLTable']] = dataclasses.field(compare=False, default_factory=lambda: lambda database: list([]))
    get_views_handler: Callable[[Self], List['SQLView']] = dataclasses.field(compare=False, default_factory=lambda: lambda database: list([]))
    get_triggers_handler: Callable[[Self], List['SQLTrigger']] = dataclasses.field(compare=False, default_factory=lambda: lambda database: list([]))

    control: Optional[wx.Control] = None

    def __post_init__(self):
        self.tables = LazyList(lambda: self.get_tables_handler(self))
        self.views = LazyList(lambda: self.get_views_handler(self))
        self.triggers = LazyList(lambda: self.get_triggers_handler(self))

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, SQLDatabase):
            return True

        if any([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare
        ]):
            return True

        return any([t1 != t2 for t1, t2 in zip(self.tables, other.tables)])


@dataclasses.dataclass
class SQLTable(abc.ABC):
    id: int
    name: str

    database: SQLDatabase = dataclasses.field(compare=False)
    engine: Optional[str]

    get_columns_handler: Callable[[Self], List['SQLColumn']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list([]))
    get_indexes_handler: Callable[[Self], List['SQLIndex']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list([]))
    get_foreign_keys_handler: Callable[[Self], List['SQLForeignKey']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list([]))
    get_records_handler: Callable[[Self, int, int], List['SQLRecord']] = dataclasses.field(compare=False, default_factory=lambda: lambda table, limit=1000, offset=0: list([]))

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

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, SQLTable):
            return True

        if any([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare
        ]):
            return True

        if any([c1 != c2 for c1, c2 in zip(self.columns, other.columns)]):
            return True

        if any([i1 != i2 for i1, i2 in zip(self.indexes, other.indexes)]):
            return True

        return False

    def copy(self):
        # # Invalidate caches to ensure fresh data from DB
        # self.columns.clear()
        # self.indexes.clear()
        # self.foreign_keys.clear()

        current_columns = list(self.columns)
        current_indexes = list(self.indexes)
        current_foreign_keys = list(self.foreign_keys)
        current_records = list(self.records)

        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_table = self.__class__(**field_values)

        new_table.columns = ObservableList([dataclasses.replace(col, table=new_table) for col in current_columns])
        new_table.indexes = ObservableList([dataclasses.replace(idx, table=new_table) for idx in current_indexes])
        new_table.foreign_keys = ObservableList([dataclasses.replace(fk) for fk in current_foreign_keys])
        new_table.records = ObservableList([dataclasses.replace(rec, table=new_table) for rec in current_records])

        return new_table

    def is_valid(self) -> bool:
        # print("table is valid:", f"name: {self.name != ''}", len(self.columns) > 0, {c.name: c.is_valid for c in self.columns},
        #
        #       )
        return all([
            self.name.strip() != "",
            not " " in self.name.strip(),
            len(self.columns) > 0,
            len(set([c.name for c in self.columns])) == len(self.columns),
            all([c.is_valid for c in self.columns]),
            all([ix.is_valid for ix in self.indexes]),
            all([fk.is_valid for fk in self.foreign_keys]),
        ])

    @staticmethod
    def generate_uuid(length: int = 8) -> str:
        return str(uuid.uuid4())[::-1][:length]

    def get_identifier_indexes(self) -> List['SQLIndex']:
        identifier_indexes = []
        for index in list(self.indexes):
            if index.type.is_primary or index.type.is_unique:
                identifier_indexes.append(index)

        return identifier_indexes

    @abc.abstractmethod
    def rename(self, table: 'SQLTable', new_name: str):
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def alter(self):
        raise NotImplementedError

    @abc.abstractmethod
    def drop(self):
        raise NotImplementedError

    def save(self) -> Optional[bool]:

        if self.id == -1:
            method = self.create
        else:
            method = self.alter

        result = method()

        if method:
            self.database.tables.refresh()

        return result


@dataclasses.dataclass
class SQLColumn(abc.ABC):
    id: int
    pos: int
    name: str
    table: SQLTable
    datatype: SQLDataType
    is_nullable: bool = False
    extra: Optional[str] = None

    server_default: Optional[str] = None

    # is_unsigned: bool = False
    # is_zerofill: bool = False
    is_auto_increment: bool = False

    # set: Optional[List[str]] = None
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
        return any([i.type == SQLiteIndexType.PRIMARY for i in list(self.table.indexes) if self.name in i.columns])

    @property
    def is_unique_key(self):
        return any([i.type == SQLiteIndexType.UNIQUE for i in list(self.table.indexes) if self.name in i.columns])

    @property
    def is_valid(self):
        if not all([self.name, self.datatype]):
            return False

        if not self.name.strip() or " " in self.name.strip():
            return False

        # try:
        if self.datatype.has_length and not self.length_scale_set:
            return False
        # except Exception as ex:
        #     print("errore", ex)

        if self.datatype.has_precision and not self.numeric_precision:
            return False

        if self.datatype.has_scale and not self.numeric_scale:
            return False

        if self.datatype.has_set and not self.set:
            return False

        return True

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
            self.is_auto_increment = False
            self.server_default = value

    @property
    def length_scale_set(self) -> str:
        candidates = [
            (self.datatype.has_length, "length", str),
            (self.datatype.has_precision, "numeric_precision", str),
            (self.datatype.has_set, "set", lambda v: ",".join(v)),
        ]

        length_scale_set = ""

        for condition, attr, transform in candidates:
            if condition:
                if value := getattr(self, attr, None):
                    length_scale_set = transform(value)

                break

        if self.datatype.has_scale:
            if scale := getattr(self, "numeric_scale", None):
                length_scale_set += f",{scale}"

        return length_scale_set

    @length_scale_set.setter
    def length_scale_set(self, value):
        candidates = [
            (self.datatype.has_length, "length", str),
            (self.datatype.has_precision, "numeric_precision", lambda value: [v.strip("'") for v in value.split(",")][0]),
            (self.datatype.has_scale, "numeric_scale", lambda value: [v.strip("'") for v in value.split(",")][1]),
            (self.datatype.has_set, "set", lambda value: [v.strip("'") for v in value.split(",")]),
        ]

        for condition, attr, transform in candidates:
            if condition:
                set_value = transform(value)

                if self.datatype.max_size is not None and set_value.isdigit() and int(set_value) > self.datatype.max_size:
                    set_value = self.datatype.max_size

                setattr(self, attr, set_value)

    @staticmethod
    def generate_uuid(length: int = 8) -> str:
        return str(uuid.uuid4())[::-1][:length]


@dataclasses.dataclass
class SQLIndex(abc.ABC):
    id: int
    pos: int
    name: str
    type: SQLIndexType
    columns: List[str]
    table: SQLTable = dataclasses.field(compare=False)
    condition: str = dataclasses.field(default_factory=str)
    expression: List[str] = dataclasses.field(default_factory=list)

    def __ne__(self, other):
        if not isinstance(other, SQLIndex):
            return True

        return any([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare
        ])

    @property
    def is_valid(self):
        return all([self.name, self.type, len(self.columns)])


@dataclasses.dataclass
class SQLForeignKey(abc.ABC):
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


@dataclasses.dataclass
class SQLRecord(abc.ABC):
    id: int
    table: 'SQLTable'
    values: Dict[str, str] = dataclasses.field(default_factory=dict)

    def is_new(self) -> bool:
        return self.id <= -1

    def is_valid(self) -> bool:
        for column in self.table.columns:
            if column.virtuality is not None:
                continue

            if column.is_nullable:
                continue

            if column.is_auto_increment or column.server_default:
                continue

            if column.datatype.name == "BOOLEAN":
                continue

            if not self.values.get(column.name):
                return False

            if not str(self.values.get(column.name)).strip():
                return False

        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SQLRecord):
            return False

        return self.values == other.values

    def _get_identifier_columns(self) -> Dict[str, str]:
        identifier_indexes = self.table.get_identifier_indexes()

        if not identifier_indexes:
            raise ValueError("Cannot identify record without primary or unique index")

        original_table = next((t for t in self.table.database.tables if t.id == self.table.id), None)
        identifier_conditions = {}
        for identifier_index in identifier_indexes:
            columns: List[SQLColumn] = [column for column in self.table.columns if column.name in identifier_index.columns]
            original_record = next((r for r in list(original_table.records) if r.id == self.id), None)

            for column in columns:
                if original_record is not None :
                    identifier_conditions[column.name] = original_record.values.get(column.name)

                if column.datatype.format is not None:
                    identifier_conditions[column.name] = column.datatype.format(identifier_conditions[column.name])

            if identifier_index.type.is_primary:
                break

        return identifier_conditions

    @abc.abstractmethod
    def insert(self):
        raise NotImplementedError

    @abc.abstractmethod
    def update(self):
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self):
        raise NotImplementedError

    @staticmethod
    def delete_many(table: SQLTable, records: List[Self]) -> bool:
        results = []
        with table.database.context.transaction() as transaction:
            for record in records:
                if record.is_new():
                    continue

                if raw_delete_record := record.raw_delete_record():
                    results.append(transaction.execute(raw_delete_record))
                    table.records.remove(record)

        return all(results)

    def save(self) -> Optional[bool]:
        if not self.is_valid():
            raise ValueError("Record is not yet valid")

        if self.is_new():
            method = self.insert
        else:
            method = self.update

        return method()


@dataclasses.dataclass
class SQLView(abc.ABC):
    id: int
    name: str
    database: SQLDatabase = dataclasses.field(compare=False)
    sql: str

    def copy(self):
        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_view = self.__class__(**field_values)

        return new_view

    @abc.abstractmethod
    def create(self):
        raise NotImplementedError

    @abc.abstractmethod
    def drop(self):
        raise NotImplementedError

    @abc.abstractmethod
    def alter(self):
        raise NotImplementedError


@dataclasses.dataclass
class SQLTrigger(abc.ABC):
    id: int
    name: str
    database: SQLDatabase = dataclasses.field(compare=False)
    sql: str
    timing: Literal['BEFORE', 'AFTER'] = 'BEFORE'
    event: Literal['INSERT', 'UPDATE', 'DELETE'] = 'INSERT'

    def copy(self):
        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_view = self.__class__(**field_values)

        return new_view
