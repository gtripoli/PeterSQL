from structures.engines.datatype import SQLDataType, StandardDataType, DataTypeCategory, DataTypeFormat


class MariaDBDataType(StandardDataType):
    # Integer types
    TINYINT = SQLDataType(name="TINYINT", category=DataTypeCategory.INTEGER, has_unsigned=True)
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER, has_unsigned=True)
    MEDIUMINT = SQLDataType(name="MEDIUMINT", category=DataTypeCategory.INTEGER, has_unsigned=True)
    INT = SQLDataType(name="INT", category=DataTypeCategory.INTEGER, alias=["INTEGER"], has_unsigned=True)
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER, has_unsigned=True)

    # Floating point
    FLOAT = SQLDataType(name="FLOAT", category=DataTypeCategory.REAL, has_precision=True)
    DOUBLE = SQLDataType(name="DOUBLE", category=DataTypeCategory.REAL, alias=["REAL"], has_precision=True)
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, alias=["DEC"], has_precision=True, has_scale=True)

    # Text types
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=255)
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=65535, format=DataTypeFormat.STRING)
    TINYTEXT = SQLDataType(name="TINYTEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)
    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)
    MEDIUMTEXT = SQLDataType(name="MEDIUMTEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)
    LONGTEXT = SQLDataType(name="LONGTEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)

    # Binary types
    BINARY = SQLDataType(name="BINARY", category=DataTypeCategory.BINARY, has_length=True, max_size=255)
    VARBINARY = SQLDataType(name="VARBINARY", category=DataTypeCategory.BINARY, has_length=True, max_size=65535)
    TINYBLOB = SQLDataType(name="TINYBLOB", category=DataTypeCategory.BINARY)
    BLOB = SQLDataType(name="BLOB", category=DataTypeCategory.BINARY)
    MEDIUMBLOB = SQLDataType(name="MEDIUMBLOB", category=DataTypeCategory.BINARY)
    LONGBLOB = SQLDataType(name="LONGBLOB", category=DataTypeCategory.BINARY)

    # Date and time
    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL)
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL)
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL)
    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL)
    YEAR = SQLDataType(name="YEAR", category=DataTypeCategory.TEMPORAL)

    ENUM = SQLDataType(name="ENUM", category=DataTypeCategory.TEXT, has_set=True)
    SET = SQLDataType(name="SET", category=DataTypeCategory.TEXT, has_set=True)

    # Other
    BOOLEAN = StandardDataType.BOOLEAN
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, format=DataTypeFormat.JSON)