import sqlalchemy as sa
import sqlalchemy.dialects
from models.structures import SQLDataType, DataTypeCategory, StandardDataType


class DataType(SQLDataType):
    has_set = False
    has_length = False


class SQLiteDataType(StandardDataType):
    INTEGER = DataType(name="INTEGER", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.INTEGER())
    REAL = DataType(name="REAL", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.REAL())
    TEXT = DataType(name="TEXT", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Text(length=kwargs.get('length')))
    BLOB = DataType(name="BLOB", category=DataTypeCategory.BINARY, has_default=False, sa_type=lambda **kwargs: sa.dialects.sqlite.BLOB())
    NUMERIC = DataType(name="NUMERIC", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Numeric(kwargs.get('length'), kwargs.get('scale')))

    VARCHAR = DataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.VARCHAR(kwargs.get('length')))
    CHAR = DataType(name="CHAR", category=DataTypeCategory.TEXT, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.CHAR(kwargs.get('length')))
    BOOLEAN = DataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Boolean())
    DATE = DataType(name="DATE", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.Date())
    DATETIME = DataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.sqlite.DateTime())
    JSON = DataType(name=" JSON", category=DataTypeCategory.TEXT, has_default=False, sa_type=lambda **kwargs: sa.dialects.sqlite.JSON())
