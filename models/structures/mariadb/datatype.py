from typing import Dict

from models.structures.datatype import StandardDataType, SQLDataType, DataTypeCategory


class MariaDBDataType(StandardDataType):
    BIT = SQLDataType(name="BIT", category=DataTypeCategory.INTEGER, max_size=64)

    TINYINT = SQLDataType(name="TINYINT", category=DataTypeCategory.INTEGER, max_size=127)
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER, max_size=32767)
    INTEGER = SQLDataType(name="INTEGER", alias=["INT"], category=DataTypeCategory.INTEGER)
    MEDIUMINT = SQLDataType(name="MEDIUMINT", category=DataTypeCategory.INTEGER, max_size=8388607)
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER, max_size=9223372036854775807)

    FLOAT = SQLDataType(name="FLOAT", category=DataTypeCategory.REAL)
    DOUBLE = SQLDataType(name="DOUBLE", category=DataTypeCategory.REAL)
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, default_length=20, default_scale=6, max_size=9223372036854775807)

    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL, format="HH:MM:SS")
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, format="YYYY-MM-DD HH:MM:SS")
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL, format="YYYY-MM-DD HH:MM:SS")

    TINYTEXT = SQLDataType(name="TINYTEXT", category=DataTypeCategory.TEXT, max_size=255)
    MEDIUMTEXT = SQLDataType(name="MEDIUMTEXT", category=DataTypeCategory.TEXT, max_size=16777215)
    LONGTEXT = SQLDataType(name="LONGTEXT", category=DataTypeCategory.TEXT, max_size=4294967295)
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, default_collation="utf8mb4_bin")

    BINARY = SQLDataType(name="BINARY", category=DataTypeCategory.BINARY, default_length=50)
    VARBINARY = SQLDataType(name="VARBINARY", category=DataTypeCategory.BINARY, default_length=50)

    TINYBLOB = SQLDataType(name="TINYBLOB", category=DataTypeCategory.BINARY, default_length=50, max_size=255)
    MEDIUMBLOB = SQLDataType(name="MEDIUMBLOB", category=DataTypeCategory.BINARY, max_size=(2 ** 24) - 1)
    LONGBLOB = SQLDataType(name="LONGBLOB", category=DataTypeCategory.BINARY, max_size=(2 ** 32) - 1)

    ENUM = SQLDataType(name="ENUM", category=DataTypeCategory.OTHER, default_set=["'Y'", "'N'"])
    SET = SQLDataType(name="SET", category=DataTypeCategory.OTHER, default_set=["'Value 1'", "'Value 2'"])

    POINT = SQLDataType(name="Point", category=DataTypeCategory.SPATIAL)
    LINESTRING = SQLDataType(name="LineString", category=DataTypeCategory.SPATIAL)
    POLYGON = SQLDataType(name="Polygon", category=DataTypeCategory.SPATIAL)
    GEOMETRY = SQLDataType(name="Geometry", category=DataTypeCategory.SPATIAL)
    MULTIPOINT = SQLDataType(name="MultiPoint", category=DataTypeCategory.SPATIAL)
    MULTILINESTRING = SQLDataType(name="MultiLineString", category=DataTypeCategory.SPATIAL)
    MULTIPOLYGON = SQLDataType(name="MultiPolygon", category=DataTypeCategory.SPATIAL)
    GEOMETRYCOLLECTION = SQLDataType(name="GeometryCollection", category=DataTypeCategory.SPATIAL)

    @classmethod
    def get_by_name(cls, col : Dict[str, str]) -> SQLDataType:  # type: ignore[override]
        name = col['DATA_TYPE']
        if name.upper() == "LONGTEXT" and str(col.get("COLLATION_NAME", "")).endswith("_bin"):
            return cls.JSON
        if name.upper() == "TINYINT" and str(col.get("COLUMN_TYPE", "")) == "tinyint(1)":
            return cls.BOOLEAN

        return super().get_by_name(name)
