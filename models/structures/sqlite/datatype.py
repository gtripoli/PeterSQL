from models.structures.datatype import SQLDataType, StandardDataType, DataTypeCategory


class DataType(SQLDataType):
    has_set = False
    has_length = False
    has_scale = False
    has_precision = False


class SQLiteDataType(StandardDataType):
    INTEGER = DataType(name="INTEGER", category=DataTypeCategory.INTEGER, alias=["INT"])
    BOOLEAN = DataType(name="BOOLEAN", category=DataTypeCategory.INTEGER)

    REAL = DataType(name="REAL", category=DataTypeCategory.REAL)
    NUMERIC = DataType(name="NUMERIC", category=DataTypeCategory.REAL, has_precision=True, has_scale=True, alias=["DECIMAL", "NUM"])

    TEXT = DataType(name="TEXT", category=DataTypeCategory.TEXT, has_length=True)
    VARCHAR = DataType(name="VARCHAR", category=DataTypeCategory.TEXT)
    CHAR = DataType(name="CHAR", category=DataTypeCategory.TEXT)
    JSON = DataType(name="JSON", category=DataTypeCategory.TEXT)

    BLOB = DataType(name="BLOB", category=DataTypeCategory.BINARY)

    DATE = DataType(name="DATE", category=DataTypeCategory.TEMPORAL)
    DATETIME = DataType(name="DATETIME", category=DataTypeCategory.TEMPORAL)
