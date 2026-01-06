import abc
import copy
import dataclasses
import datetime
import uuid

from typing import Optional, Callable, Literal, List, Self, Dict

import wx

from icons import BitmapList
from helpers.observables import ObservableLazyList

from structures.engines.datatype import SQLDataType
from structures.engines.indextype import SQLIndexType
from structures.engines.sqlite.indextype import SQLiteIndexType


@dataclasses.dataclass(eq=False)
class SQLDatabase(abc.ABC):
    id: Optional[int]
    name: str
    context: 'AbstractContext'
    total_bytes: float = 0

    get_tables_handler: Callable[[Self], List['SQLTable']] = dataclasses.field(compare=False, default_factory=lambda: lambda database: list([]))
    get_views_handler: Optional[Callable[[Self], List['SQLView']]] = dataclasses.field(compare=False, default=None)
    get_procedures_handler: Optional[Callable[[Self], List['SQLProcedure']]] = dataclasses.field(compare=False, default=None)
    get_functions_handler: Optional[Callable[[Self], List['SQLFunction']]] = dataclasses.field(compare=False, default=None)
    get_triggers_handler: Optional[Callable[[Self], List['SQLTrigger']]] = dataclasses.field(compare=False, default=None)
    get_events_handler: Optional[Callable[[Self], List['SQLEvent']]] = dataclasses.field(compare=False, default=None)

    def __post_init__(self):
        self.tables = ObservableLazyList(lambda db=self: self.get_tables_handler(db))
        if callable(self.get_views_handler):
            self.views = ObservableLazyList(lambda db=self: self.get_views_handler(db))

        if callable(self.get_procedures_handler):
            self.procedures = ObservableLazyList(lambda db=self: self.get_procedures_handler(db))

        if callable(self.get_functions_handler):
            self.functions = ObservableLazyList(lambda db=self: self.get_functions_handler(db))

        if callable(self.get_triggers_handler):
            self.triggers = ObservableLazyList(lambda db=self: self.get_triggers_handler(db))

        if callable(self.get_events_handler):
            self.events = ObservableLazyList(lambda db=self: self.get_events_handler(db))

    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, SQLDatabase):
            return False

        if not all([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare and not isinstance(field, ObservableLazyList)
        ]):
            return False

        for observable_lazy_list in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            if not all([oll1 != oll2 for oll1, oll2 in zip(getattr(self, observable_lazy_list, None), getattr(other, observable_lazy_list, None))]):
                return False

        return True

    def refresh(self):
        original_database = next((d for d in self.context.databases.get_value() if d.id == self.id), None)

        for observable_lazy_list_name in ["tables", "views", "procedures", "functions", "triggers", "events"]:
            if getattr(self, observable_lazy_list_name, None) != (observable_lazy_list := getattr(original_database, observable_lazy_list_name, None)):
                observable_lazy_list.refresh()


@dataclasses.dataclass(eq=False)
class SQLTable(abc.ABC):
    id: int
    name: str

    database: SQLDatabase = dataclasses.field(compare=False)
    engine: Optional[str] = None

    total_bytes: float = 0
    total_rows: Optional[int] = None
    auto_increment: Optional[int] = 0
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    comment: Optional[str] = None
    collation_name: Optional[str] = None

    get_columns_handler: Callable[[Self], List['SQLColumn']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list())
    get_indexes_handler: Callable[[Self], List['SQLIndex']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list())
    get_foreign_keys_handler: Callable[[Self], List['SQLForeignKey']] = dataclasses.field(compare=False, default_factory=lambda: lambda table: list())
    get_records_handler: Callable[[Self, Optional[str], int, int, Optional[str]], List['SQLRecord']] = dataclasses.field(compare=False, default_factory=lambda: lambda table, filters=None, limit=1000, offset=0, orders=None: list())

    def __post_init__(self):
        self.indexes = ObservableLazyList(lambda: self.get_indexes_handler(self))
        self.columns = ObservableLazyList(lambda: self.get_columns_handler(self))
        self.foreign_keys = ObservableLazyList(lambda: self.get_foreign_keys_handler(self))

    def load_records(self, filters: Optional[str] = None, limit: int = 1000, offset: int = 0, orders: Optional[str] = None):
        self.records = ObservableLazyList(lambda: self.get_records_handler(self, filters, limit, offset, orders))

    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, SQLTable):
            return False

        # print("== SQLTable", {
        #     field.name: (getattr(self, field.name), getattr(other, field.name))
        #     for field in dataclasses.fields(self)
        #     if field.compare and not isinstance(field, ObservableLazyList)
        # })

        if not self.compare_fields(other):
            return False

        for observable_lazy_list_name in ["columns", "indexes", "foreign_keys"]:
            if getattr(other, observable_lazy_list_name) != getattr(self, observable_lazy_list_name):
                return False

        return True

    def compare_fields(self, other: Self):
        return all([
            getattr(self, field.name) == getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare and not isinstance(field, ObservableLazyList)
        ])

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

    @property
    def is_valid(self) -> bool:
        if not self.name.strip():
            return False

        if " " in self.name.strip():
            return False

        if not self.columns:
            return False

        if len(self.columns) != len(set([c.name for c in self.columns])):
            return False

        for c in self.columns:
            if not c.is_valid:
                return False

        for ix in self.indexes:
            if not ix.is_valid:
                return False

        for fk in self.foreign_keys:
            if not fk.is_valid:
                return False

        return True

    @property
    def is_new(self):
        return self.id <= -1

    @staticmethod
    def generate_uuid(length: int = 8) -> str:
        return str(uuid.uuid4())[::-1][:length]

    def get_identifier_indexes(self) -> List['SQLIndex']:
        identifier_indexes = []
        for index in list(self.indexes):
            if index.type.is_primary or index.type.is_unique:
                identifier_indexes.append(index)

        return identifier_indexes

    def copy(self):
        cls = self.__class__
        field_values = {f.name: getattr(self, f.name) for f in dataclasses.fields(cls)}
        new_cls = cls(**field_values)

        for observable_lazy_list_name in ["columns", "indexes", "foreign_keys"]:
            o1: ObservableLazyList = getattr(self, observable_lazy_list_name)
            o2: ObservableLazyList = getattr(new_cls, observable_lazy_list_name)

            if not o1.is_loaded:
                o1.refresh()

            o2._value = copy.copy(o1._value)
            o2._loaded = True
            o2._callbacks = o1._callbacks

        return new_cls

    def refresh(self):
        original_table = next((t for t in self.database.tables if t.id == self.id), None)

        for observable_lazy_list_name in ["columns", "indexes", "foreign_keys"]:
            if (observable_lazy_list := getattr(original_table, observable_lazy_list_name)) != getattr(self, observable_lazy_list_name):
                observable_lazy_list.refresh()

    def save(self) -> Optional[bool]:
        if self.is_new:
            self.create()
            self.database.refresh()
        else:
            self.alter()
            self.refresh()

        return True


@dataclasses.dataclass(eq=False)
class SQLColumn(abc.ABC):
    id: int
    name: str
    table: SQLTable = dataclasses.field(compare=False)
    datatype: SQLDataType
    is_nullable: bool = False
    extra: Optional[str] = None

    server_default: Optional[str] = None
    is_auto_increment: bool = False
    length: Optional[int] = None

    check: Optional[str] = None
    collation_name: Optional[str] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    datetime_precision: Optional[int] = None
    virtuality: Optional[Literal["VIRTUAL", "STORED"]] = None
    expression: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, SQLColumn):
            return False

        for field in dataclasses.fields(self):
            if not field.compare:
                continue

            if getattr(self, field.name) != getattr(other, field.name):
                return False

        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, datatype={self.datatype}, is_nullable={self.is_nullable})"

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

        if self.datatype.has_length and not self.length_scale_set:
            return False

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

    def copy(self):
        cls = self.__class__
        field_values = {f.name: getattr(self, f.name) for f in dataclasses.fields(cls)}
        return cls(**field_values)


@dataclasses.dataclass(eq=False)
class SQLIndex(abc.ABC):
    id: int
    name: str
    type: SQLIndexType
    columns: List[str]
    table: SQLTable = dataclasses.field(compare=False)
    condition: str = dataclasses.field(default_factory=str)
    expression: List[str] = dataclasses.field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, SQLIndex):
            return False

        for field in dataclasses.fields(self):
            if not field.compare:
                continue

            if getattr(self, field.name) != getattr(other, field.name):
                return False

        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, type={self.type}, columns={self.columns})"

    @property
    def is_valid(self):
        return all([self.name, self.type, len(self.columns)])

    def copy(self):
        cls = self.__class__
        field_values = {f.name: getattr(self, f.name) for f in dataclasses.fields(cls)}
        return cls(**field_values)


@dataclasses.dataclass(eq=False)
class SQLForeignKey(abc.ABC):
    id: int
    name: str
    table: SQLTable = dataclasses.field(compare=False)
    columns: List[str]
    reference_table: str
    reference_columns: List[str]

    on_update: str
    on_delete: str

    bitmap: wx.Bitmap = dataclasses.field(init=False)

    def __post_init__(self):
        self.bitmap = BitmapList.KEY_FOREIGN

    def __eq__(self, other):
        if not isinstance(other, SQLForeignKey):
            return False

        if not all([
            getattr(self, field.name) != getattr(other, field.name)
            for field in dataclasses.fields(self)
            if field.compare
        ]):
            return False

        return True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, columns={self.columns}, reference_table={self.reference_table}, reference_columns={self.reference_columns})"

    @property
    def is_valid(self):
        return all([self.name, len(self.columns), self.reference_table, len(self.reference_columns)])

    def copy(self):
        cls = self.__class__
        field_values = {f.name: getattr(self, f.name) for f in dataclasses.fields(cls)}
        return cls(**field_values)


@dataclasses.dataclass(eq=False)
class SQLRecord(abc.ABC):
    id: int
    table: 'SQLTable'
    values: Dict[str, str] = dataclasses.field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SQLRecord):
            return False

        return self.values == other.values

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, table={self.table.name}, values={self.values})"

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
                if original_record is not None:
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


@dataclasses.dataclass(eq=False)
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


@dataclasses.dataclass(eq=False)
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


@dataclasses.dataclass(eq=False)
class SQLProcedure(abc.ABC):
    id: int
    name: str
    database: SQLDatabase = dataclasses.field(compare=False)

    def copy(self):
        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_view = self.__class__(**field_values)

        return new_view


@dataclasses.dataclass(eq=False)
class SQLFunction(abc.ABC):
    id: int
    name: str
    database: SQLDatabase = dataclasses.field(compare=False)

    def copy(self):
        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_view = self.__class__(**field_values)

        return new_view


@dataclasses.dataclass(eq=False)
class SQLEvent(abc.ABC):
    id: int
    name: str
    database: SQLDatabase = dataclasses.field(compare=False)

    def copy(self):
        field_values = {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        new_view = self.__class__(**field_values)

        return new_view
