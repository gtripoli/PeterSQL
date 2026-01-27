from structures.engines.datatype import (
    DataTypeCategory,
    DataTypeFormat,
    SQLDataType,
    StandardDataType,
)


class PostgreSQLDataType(StandardDataType):
    # Integer types
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER, alias=["INT"], format=DataTypeFormat.INTEGER)
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)

    # Serial types (auto-incrementing)
    SMALLSERIAL = SQLDataType(name="SMALLSERIAL", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)
    SERIAL = SQLDataType(name="SERIAL", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)
    BIGSERIAL = SQLDataType(name="BIGSERIAL", category=DataTypeCategory.INTEGER, format=DataTypeFormat.INTEGER)

    # Floating point
    REAL = SQLDataType(name="REAL", category=DataTypeCategory.REAL, format=DataTypeFormat.REAL)
    DOUBLE_PRECISION = SQLDataType(name="DOUBLE PRECISION", category=DataTypeCategory.REAL, alias=["FLOAT8"], format=DataTypeFormat.REAL)

    # Decimal
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, alias=["NUMERIC"], has_precision=True, has_scale=True, format=DataTypeFormat.REAL)

    # Text types
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=10485760, format=DataTypeFormat.STRING)
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True, max_size=10485760, format=DataTypeFormat.STRING, alias=["CHARACTER VARYING"])
    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)

    # Binary types
    BYTEA = SQLDataType(name="BYTEA", category=DataTypeCategory.BINARY)

    # Boolean
    BOOLEAN = SQLDataType(name="BOOLEAN", category=DataTypeCategory.INTEGER, alias=["BOOL"], format=DataTypeFormat.BOOLEAN)

    # Date and time
    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.STRING)
    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.STRING)
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.STRING)
    TIMESTAMPTZ = SQLDataType(name="TIMESTAMPTZ", category=DataTypeCategory.TEMPORAL, alias=["TIMESTAMP WITH TIME ZONE"], format=DataTypeFormat.STRING)
    INTERVAL = SQLDataType(name="INTERVAL", category=DataTypeCategory.TEMPORAL, format=DataTypeFormat.STRING)

    # JSON
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, format=DataTypeFormat.JSON)
    JSONB = SQLDataType(name="JSONB", category=DataTypeCategory.TEXT, format=DataTypeFormat.JSON)

    # UUID
    UUID = SQLDataType(name="UUID", category=DataTypeCategory.TEXT, format=DataTypeFormat.STRING)
