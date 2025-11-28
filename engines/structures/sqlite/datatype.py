from engines.structures.datatype import SQLDataType, StandardDataType, DataTypeCategory, DataTypeFormat


class SQLiteDataType(StandardDataType):
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER, alias=["INT"], has_precision=False)

    TINYINT = SQLDataType(name="TINYINT", category=DataTypeCategory.INTEGER)
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER)
    MEDIUMINT = SQLDataType(name="MEDIUMINT", category=DataTypeCategory.INTEGER)
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER)
    INTEGER2 = SQLDataType(name="INT2", category=DataTypeCategory.INTEGER)
    INTEGER8 = SQLDataType(name="INT8", category=DataTypeCategory.INTEGER)

    CHARACTER = SQLDataType(name="CHARACTER", category=DataTypeCategory.TEXT, has_length=True, max_size=20)

    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=255, format=DataTypeFormat.STRING)
    NCHAR = SQLDataType(name="NCHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=55, format=DataTypeFormat.STRING)
    NVARCHAR = SQLDataType(name="NVARCHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=100, format=DataTypeFormat.STRING)
    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)
    CLOB = SQLDataType(name="CLOB", category=DataTypeCategory.TEXT)

    REAL = SQLDataType(name="REAL", category=DataTypeCategory.REAL)
    DOUBLE = SQLDataType(name="DOUBLE", category=DataTypeCategory.REAL)
    FLOAT = SQLDataType(name="FLOAT", category=DataTypeCategory.REAL)

    NUMERIC = SQLDataType(name="NUMERIC", category=DataTypeCategory.REAL)
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, has_precision=True, has_scale=True)
    BOOLEAN = StandardDataType.BOOLEAN