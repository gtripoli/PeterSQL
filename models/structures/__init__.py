import abc
import enum
import dataclasses
import sqlalchemy as sa
from typing import List, Callable


class DataTypeCategory(enum.Enum):
    TEXT = "TEXT"
    BINARY = "BINARY"
    INTEGER = "INTEGER"
    REAL = "REAL"
    SPATIAL = "SPATIAL"
    TEMPORAL = "TEMPORAL"
    OTHER = "OTHER"


class DataTypeCategoryColor(enum.Enum):
    TEXT = (23, 139, 23)
    BINARY = (190, 44, 130)
    INTEGER = (0, 0, 255)
    REAL = (83, 80, 255)
    SPATIAL = (125, 151, 143)
    TEMPORAL = (190, 46, 31)
    OTHER = (148, 147, 29)


@dataclasses.dataclass
class SQLDataType:
    name: str
    category: DataTypeCategory
    has_default: bool
    sa_type: Callable[..., sa.types.TypeEngine]
    # alias: Optional[List[str]] = None
    max_size: int = None
    default_set: List[str] = ""
    default_length: int = 10
    default_scale: int = 5
    format: str = None

    has_set: bool = dataclasses.field(default=None)
    has_scale: bool = dataclasses.field(default=None)
    has_length: bool = dataclasses.field(default=None)
    has_precision: bool = dataclasses.field(default=None)
    has_collation: bool = dataclasses.field(default=None)
    has_display_width: bool = dataclasses.field(default=None)

    has_zerofill: bool = dataclasses.field(default=None)
    has_unsigned: bool = dataclasses.field(default=None)

    def __post_init__(self):

        if self.has_set is None:
            object.__setattr__(self, "has_set", self.name in ["ENUM", "SET"])

        if self.has_length is None:
            object.__setattr__(self, "has_length", self.category in [DataTypeCategory.TEXT])
        if self.has_display_width is None:
            object.__setattr__(self, "has_display_width", self.category in [DataTypeCategory.INTEGER])
        if self.has_precision is None:
            object.__setattr__(self, "has_precision", self.category in [DataTypeCategory.REAL])
        if self.has_scale is None:
            object.__setattr__(self, "has_scale", self.has_precision)
        if self.has_collation is None:
            object.__setattr__(self, "has_collation", self.category in [DataTypeCategory.TEXT])
        if self.has_zerofill is None:
            object.__setattr__(self, "has_zerofill", self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])
        if self.has_unsigned is None:
            object.__setattr__(self, "has_unsigned", self.category in [DataTypeCategory.INTEGER, DataTypeCategory.REAL])


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

    @classmethod
    def get_all(cls) -> List[SQLDataType]:
        types = [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), SQLDataType)
        ]

        return sorted(types, key=lambda t: list(DataTypeCategory).index(t.category))

    @classmethod
    def get_by_name(cls, name: str) -> SQLDataType:
        for datatype in cls.get_all():
            if name == datatype.name:
                return datatype
        return cls.VARCHAR

    @classmethod
    def get_by_type(cls, type: sa.types.TypeEngine) -> SQLDataType:
        name = type.__visit_name__.upper()

        return cls.get_by_name(name)
