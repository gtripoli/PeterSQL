from models.structures.datatype import StandardDataType, SQLDataType, DataTypeCategory


class PostgreSQLDataType(StandardDataType):
    # Integer types
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER, max_size=32767)
    INTEGER = SQLDataType(name="INTEGER", alias=["INT", "INT4"], category=DataTypeCategory.INTEGER, max_size=2147483647)
    BIGINT = SQLDataType(name="BIGINT", alias=["INT8"], category=DataTypeCategory.INTEGER, max_size=9223372036854775807)

    # Serial types (auto-incrementing)
    SMALLSERIAL = SQLDataType(name="SMALLSERIAL", category=DataTypeCategory.INTEGER, max_size=32767)
    SERIAL = SQLDataType(name="SERIAL", category=DataTypeCategory.INTEGER, max_size=2147483647)
    BIGSERIAL = SQLDataType(name="BIGSERIAL", category=DataTypeCategory.INTEGER, max_size=9223372036854775807)

    # Real types
    REAL = SQLDataType(name="REAL", alias=["FLOAT4"], category=DataTypeCategory.REAL)
    DOUBLE_PRECISION = SQLDataType(name="DOUBLE PRECISION", alias=["FLOAT8"], category=DataTypeCategory.REAL)
    NUMERIC = SQLDataType(name="NUMERIC", alias=["DECIMAL"], category=DataTypeCategory.REAL, default_length=10, default_scale=2, max_size=9223372036854775807)
    MONEY = SQLDataType(name="MONEY", category=DataTypeCategory.REAL)

    # Character types
    CHARACTER = SQLDataType(name="CHARACTER", alias=["CHAR"], category=DataTypeCategory.TEXT, default_length=1, max_size=10485760)
    CHARACTER_VARYING = SQLDataType(name="CHARACTER VARYING", alias=["VARCHAR"], category=DataTypeCategory.TEXT, default_length=255, max_size=10485760)
    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT, has_length=False, max_size=1073741824)

    # Binary types
    BYTEA = SQLDataType(name="BYTEA", category=DataTypeCategory.BINARY, has_length=False)

    # Date/Time types
    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL, format="YYYY-MM-DD")
    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL, format="HH:MM:SS")
    TIME_WITH_TIME_ZONE = SQLDataType(name="TIME WITH TIME ZONE", alias=["TIMETZ"], category=DataTypeCategory.TEMPORAL, format="HH:MM:SS+TZ")
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL, format="YYYY-MM-DD HH:MM:SS")
    TIMESTAMP_WITH_TIME_ZONE = SQLDataType(name="TIMESTAMP WITH TIME ZONE", alias=["TIMESTAMPTZ"], category=DataTypeCategory.TEMPORAL, format="YYYY-MM-DD HH:MM:SS+TZ")
    INTERVAL = SQLDataType(name="INTERVAL", category=DataTypeCategory.TEMPORAL)

    # Boolean type
    BOOLEAN = SQLDataType(name="BOOLEAN", category=DataTypeCategory.INTEGER)

    # Geometric types
    POINT = SQLDataType(name="POINT", category=DataTypeCategory.SPATIAL)
    LINE = SQLDataType(name="LINE", category=DataTypeCategory.SPATIAL)
    LSEG = SQLDataType(name="LSEG", category=DataTypeCategory.SPATIAL)
    BOX = SQLDataType(name="BOX", category=DataTypeCategory.SPATIAL)
    PATH = SQLDataType(name="PATH", category=DataTypeCategory.SPATIAL)
    POLYGON = SQLDataType(name="POLYGON", category=DataTypeCategory.SPATIAL)
    CIRCLE = SQLDataType(name="CIRCLE", category=DataTypeCategory.SPATIAL)

    # Network address types
    CIDR = SQLDataType(name="CIDR", category=DataTypeCategory.OTHER)
    INET = SQLDataType(name="INET", category=DataTypeCategory.OTHER)
    MACADDR = SQLDataType(name="MACADDR", category=DataTypeCategory.OTHER)
    MACADDR8 = SQLDataType(name="MACADDR8", category=DataTypeCategory.OTHER)

    # UUID type
    UUID = SQLDataType(name="UUID", category=DataTypeCategory.OTHER)

    # JSON types
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.OTHER)
    JSONB = SQLDataType(name="JSONB", category=DataTypeCategory.OTHER)

    # Array type (special handling needed)
    ARRAY = SQLDataType(name="ARRAY", category=DataTypeCategory.OTHER)

    # Range types
    INT4RANGE = SQLDataType(name="INT4RANGE", category=DataTypeCategory.OTHER)
    INT8RANGE = SQLDataType(name="INT8RANGE", category=DataTypeCategory.OTHER)
    NUMRANGE = SQLDataType(name="NUMRANGE", category=DataTypeCategory.OTHER)
    TSRANGE = SQLDataType(name="TSRANGE", category=DataTypeCategory.OTHER)
    TSTZRANGE = SQLDataType(name="TSTZRANGE", category=DataTypeCategory.OTHER)
    DATERANGE = SQLDataType(name="DATERANGE", category=DataTypeCategory.OTHER)

    # Text search types
    TSVECTOR = SQLDataType(name="TSVECTOR", category=DataTypeCategory.OTHER)
    TSQUERY = SQLDataType(name="TSQUERY", category=DataTypeCategory.OTHER)

    # XML type
    XML = SQLDataType(name="XML", category=DataTypeCategory.OTHER)

    @classmethod
    def get_by_name(cls, column_info: dict) -> SQLDataType:  # type: ignore[override]
        """Get data type from column information dictionary"""
        data_type = column_info.get('data_type', '').upper()

        # Handle array types
        if data_type.endswith('[]'):
            return cls.ARRAY

        # Handle user-defined types or domains
        if data_type == 'USER-DEFINED':
            udt_name = column_info.get('udt_name', '').upper()
            if udt_name:
                return getattr(cls, udt_name, cls.TEXT)

        # Direct mapping
        return getattr(cls, data_type.replace(' ', '_').replace('-', '_'), cls.TEXT)
