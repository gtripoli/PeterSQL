import enum
import functools
import dataclasses

from typing import List, Callable, NamedTuple, Tuple, Dict, Optional


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


@dataclasses.dataclass
class SQLDataType:
    name: str
    category: DataTypeCategory

    alias: List[str] = dataclasses.field(default_factory=list)
    max_size: Optional[int] = None

    format: Optional[str] = None

    default_set: List[str] = dataclasses.field(default_factory=list)
    default_length: int = 50  # for the text
    default_precision: int = 10  # for the integer/boolean
    default_scale: int = 5  # for the real
    default_collation: Optional[str] = None

    has_set: Optional[bool] = dataclasses.field(default=None)  # for the enum and set
    has_length: Optional[bool] = dataclasses.field(default=None)  # for the text
    has_scale: Optional[bool] = dataclasses.field(default=None)  # for the real
    has_precision: Optional[bool] = dataclasses.field(default=None)  # for the integer
    has_collation: Optional[bool] = dataclasses.field(default=None)  # for the text

    has_zerofill: Optional[bool] = dataclasses.field(default=None)  # for the integer and real
    has_unsigned: Optional[bool] = dataclasses.field(default=None)  # for the integer and real

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
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER)
    BOOLEAN = SQLDataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, has_precision=False, has_unsigned=False)

    REAL = SQLDataType(name="REAL", category=DataTypeCategory.REAL)
    NUMERIC = SQLDataType(name="NUMERIC", category=DataTypeCategory.REAL)

    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT)
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT)
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT)

    BLOB = SQLDataType(name="BLOB", category=DataTypeCategory.BINARY)

    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL)
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL)

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
