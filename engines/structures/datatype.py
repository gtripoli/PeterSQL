import enum
import datetime
import functools
import dataclasses

from typing import List, Callable, NamedTuple, Tuple, Dict, Optional, Any


class Category(NamedTuple):
    name: str
    color: Tuple[int, int, int]
    description: Optional[str] = None


class DataTypeCategory(enum.Enum):
    TEXT = Category(name="Text", color=(23, 139, 23))
    BINARY = Category(name="Binary", color=(190, 44, 130))
    INTEGER = Category(name="Integer", color=(0, 0, 255))
    REAL = Category(name="Real", color=(83, 80, 255))
    SPATIAL = Category(name="Spatial", color=(125, 151, 143))
    TEMPORAL = Category(name="Temporal", color=(190, 46, 31))
    OTHER = Category(name="Other", color=(148, 147, 29))


class DataTypeFormat(enum.Enum):
    TEXT = lambda value: f"'{value}'"
    INTEGER = lambda value: int(value)
    BOOLEAN = lambda value: 1 if bool(value == 1) else 0
    REAL = lambda value: float(value)
    DATE = lambda value: f"'{value}'"
    DATETIME = lambda value: f"'{value}'"
    TIMESTAMP = lambda value: f"'{value}'"
    TIME = lambda value: f"'{value}'"
    JSON = lambda value: f"'{value}'"


@dataclasses.dataclass
class SQLDataType:
    name: str
    category: DataTypeCategory

    alias: List[str] = dataclasses.field(default_factory=list)
    max_size: Optional[int] = None

    format: Optional[DataTypeFormat] = dataclasses.field(default=None)

    default_set: List[str] = dataclasses.field(default_factory=list)
    default_length: int = 50  # for the text
    default_precision: int = 10  # for the integer/boolean
    default_scale: int = 5  # for the real
    default_collation: Optional[str] = None

    has_set: bool = dataclasses.field(default=False)  # for the enum and set
    has_length: bool = dataclasses.field(default=False)  # for the text
    has_scale: bool = dataclasses.field(default=False)  # for the real
    has_precision: bool = dataclasses.field(default=False)  # for the integer
    has_collation: bool = dataclasses.field(default=False)  # for the text

    has_zerofill: bool = dataclasses.field(default=False)  # for the integer and real
    has_unsigned: bool = dataclasses.field(default=False)  # for the integer and real

    def __post_init__(self):
        if self.has_set is None:
            object.__setattr__(self, "has_set", self.name in ["ENUM", "SET"])

        if self.has_length is None:
            object.__setattr__(self, "has_length", self.name in ["VARCHAR"])

        if self.has_precision is None:
            object.__setattr__(self, "has_precision", self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])

        if self.has_scale is None:
            object.__setattr__(self, "has_scale", self.has_precision and self.category in [DataTypeCategory.REAL])

        if self.has_collation is None:
            object.__setattr__(self, "has_collation", self.category in [DataTypeCategory.TEXT])

        if self.has_zerofill is None:
            object.__setattr__(self, "has_zerofill", self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])

        if self.has_unsigned is None:
            object.__setattr__(self, "has_unsigned", self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])

    def __str__(self):
        return self.name


class StandardDataType():
    BOOLEAN = SQLDataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, format=DataTypeFormat.BOOLEAN)
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)

    # NUMERIC = SQLDataType(name="NUMERIC", category=DataTypeCategory.INTEGER, has_precision=False, has_scale=False, alias=["DECIMAL", "NUM"], format=SQLDataTypeFormat.INTEGER)
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, has_precision=True, has_scale=True, format=DataTypeFormat.REAL)

    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.TEXT)
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True, format=DataTypeFormat.TEXT)
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT, format=DataTypeFormat.TEXT)
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, format=DataTypeFormat.TEXT)

    BLOB = SQLDataType(name="BLOB", category=DataTypeCategory.BINARY)

    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.DATE)
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.DATETIME)
    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.TIME)
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.TIMESTAMP)

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_all(cls) -> List[SQLDataType]:
        types = [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), SQLDataType)
        ]

        category_order = {cat: i for i, cat in enumerate(DataTypeCategory)}

        return sorted(types, key=lambda t: category_order[t.category])

    @classmethod
    def get_by_name(cls, name: str) -> SQLDataType:
        name_upper = name.upper()
        for datatype in cls.get_all():
            if datatype.name == name_upper:
                return datatype
            if any(alias == name.upper() for alias in datatype.alias):
                return datatype
        raise ValueError(f"datatype name={name_upper} not found")
