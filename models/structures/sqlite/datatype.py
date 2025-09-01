import sqlalchemy as sa
import sqlalchemy.dialects
from models.structures import SQLDataType, DataTypeCategory, StandardDataType


class DataType(SQLDataType):
    has_set = False
    has_length = False
    has_scale = False


class SQLiteDataType(StandardDataType):
    INTEGER = DataType(name="INTEGER", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.INTEGER())
    BOOLEAN = DataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Boolean())

    REAL = DataType(name="REAL", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.REAL())
    NUMERIC = DataType(name="NUMERIC", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Numeric(**kwargs))

    TEXT = DataType(name="TEXT", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.TEXT(**kwargs))
    VARCHAR = DataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.VARCHAR(**kwargs))
    CHAR = DataType(name="CHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.CHAR(**kwargs))
    JSON = DataType(name=" JSON", category=DataTypeCategory.TEXT, has_default=False, sa_type=lambda **kwargs: sa.dialects.sqlite.JSON())

    BLOB = DataType(name="BLOB", category=DataTypeCategory.BINARY, has_default=False, sa_type=lambda **kwargs: sa.dialects.sqlite.BLOB())

    DATE = DataType(name="DATE", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Date())
    DATETIME = DataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.DateTime())
