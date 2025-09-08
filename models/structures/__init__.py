import abc
import enum
import dataclasses
import functools

import sqlalchemy as sa
from typing import List, Callable, NamedTuple, Tuple, Dict, Optional


class Category(NamedTuple):
    name: str
    color: Tuple[int, int, int]
    description: str = None


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
    has_default: bool
    sa_type: Callable[..., sa.types.TypeEngine]
    alias: List[str] = dataclasses.field(default_factory=list)
    max_size: Optional[int] = None
    default_set: List[str] = dataclasses.field(default_factory=list)

    format: str = None

    default_length: int = 50  # for the text
    default_precision: int = 10  # for the integer
    default_scale: int = 5  # for the real

    has_set: bool = dataclasses.field(default=None)
    has_length: bool = dataclasses.field(default=None)  # for the text
    has_scale: bool = dataclasses.field(default=None)  # for the real
    has_precision: bool = dataclasses.field(default=None)  # for the integer
    has_collation: bool = dataclasses.field(default=None)

    has_zerofill: bool = dataclasses.field(default=None)
    has_unsigned: bool = dataclasses.field(default=None)

    def __post_init__(self):
        object.__setattr__(self, "has_set", self.has_set or self.name in ["ENUM", "SET"])
        object.__setattr__(self, "has_length", self.has_length or self.category in [DataTypeCategory.TEXT])
        object.__setattr__(self, "has_precision", self.has_precision or self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])
        object.__setattr__(self, "has_scale", self.has_scale or self.has_precision and self.category in [DataTypeCategory.REAL])
        object.__setattr__(self, "has_collation", self.has_collation or self.category in [DataTypeCategory.TEXT])
        object.__setattr__(self, "has_zerofill", self.has_zerofill or self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])
        object.__setattr__(self, "has_unsigned", self.has_unsigned or self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])

    def __str__(self):
        return self.name


class StandardDataType():
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.INTEGER())
    BOOLEAN = SQLDataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.Boolean())

    REAL = SQLDataType(name="REAL", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.REAL(**kwargs))
    NUMERIC = SQLDataType(name="NUMERIC", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.Numeric(**kwargs))

    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.Text(**kwargs))
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.VARCHAR(**kwargs))
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.CHAR(**kwargs))
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, has_default=False, sa_type=lambda **kwargs: sa.JSON())

    BLOB = SQLDataType(name="BLOB", category=DataTypeCategory.BINARY, has_default=False, sa_type=lambda **kwargs: sa.BLOB())

    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.Date())
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.DateTime())

    _category_order = {cat: i for i, cat in enumerate(DataTypeCategory)}

    @classmethod
    @functools.lru_cache(maxsize=1)
    def _map_by_name(cls) -> Dict[str, SQLDataType]:
        return {t.name: t for t in cls.get_all()}

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_all(cls) -> List[SQLDataType]:
        types = [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), SQLDataType)
        ]

        return sorted(types, key=lambda t: cls._category_order[t.category])

    @classmethod
    def get_by_name(cls, name: str) -> Optional['SQLDataType']:
        name_upper = name.upper()
        for datatype in cls.get_all():
            if datatype.name == name_upper:
                return datatype
            if any(alias == name.upper() for alias in datatype.alias):
                return datatype
        return None

    @classmethod
    def get_by_type(cls, type: sa.types.TypeEngine) -> SQLDataType:
        return cls.get_by_name(type.__visit_name__.upper())
