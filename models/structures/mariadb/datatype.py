from typing import Dict

from models.structures.datatype import StandardDataType, SQLDataType, DataTypeCategory


class MariaDBDataType(StandardDataType):
    # Integer types
    TINYINT = SQLDataType(name="TINYINT", category=DataTypeCategory.INTEGER, alias=["BOOL", "BOOLEAN"])
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER)
    MEDIUMINT = SQLDataType(name="MEDIUMINT", category=DataTypeCategory.INTEGER)
    INTEGER = SQLDataType(name="INTEGER", category=DataTypeCategory.INTEGER, alias=["INT"])
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER)

    # Real types
    FLOAT = SQLDataType(name="FLOAT", category=DataTypeCategory.REAL, has_precision=True, has_scale=True)
    DOUBLE = SQLDataType(name="DOUBLE", category=DataTypeCategory.REAL, alias=["REAL"], has_precision=True, has_scale=True)
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, alias=["NUMERIC", "DEC"], has_precision=True, has_scale=True)

    # Text types
    CHAR = SQLDataType(name="CHAR", category=DataTypeCategory.TEXT, has_length=True)
    VARCHAR = SQLDataType(name="VARCHAR", category=DataTypeCategory.TEXT, has_length=True)
    TINYTEXT = SQLDataType(name="TINYTEXT", category=DataTypeCategory.TEXT)
    TEXT = SQLDataType(name="TEXT", category=DataTypeCategory.TEXT)
    MEDIUMTEXT = SQLDataType(name="MEDIUMTEXT", category=DataTypeCategory.TEXT)
    LONGTEXT = SQLDataType(name="LONGTEXT", category=DataTypeCategory.TEXT)
    JSON = SQLDataType(name="JSON", category=DataTypeCategory.TEXT, default_collation="utf8mb4_bin")

    # Binary types
    BINARY = SQLDataType(name="BINARY", category=DataTypeCategory.BINARY, has_length=True)
    VARBINARY = SQLDataType(name="VARBINARY", category=DataTypeCategory.BINARY, has_length=True)
    TINYBLOB = SQLDataType(name="TINYBLOB", category=DataTypeCategory.BINARY)
    BLOB = SQLDataType(name="BLOB", category=DataTypeCategory.BINARY)
    MEDIUMBLOB = SQLDataType(name="MEDIUMBLOB", category=DataTypeCategory.BINARY)
    LONGBLOB = SQLDataType(name="LONGBLOB", category=DataTypeCategory.BINARY)

    # Enum and Set
    ENUM = SQLDataType(name="ENUM", category=DataTypeCategory.OTHER, has_set=True, default_set=["'Y'", "'N'"])
    SET = SQLDataType(name="SET", category=DataTypeCategory.OTHER, has_set=True, default_set=["'Value 1'", "'Value 2'"])

    # Temporal types
    DATE = SQLDataType(name="DATE", category=DataTypeCategory.TEMPORAL)
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL)
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL)
    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL)
    YEAR = SQLDataType(name="YEAR", category=DataTypeCategory.TEMPORAL)

    # Spatial
    POINT = SQLDataType(name="Point", category=DataTypeCategory.SPATIAL)
    LINESTRING = SQLDataType(name="LineString", category=DataTypeCategory.SPATIAL)
    POLYGON = SQLDataType(name="Polygon", category=DataTypeCategory.SPATIAL)
    GEOMETRY = SQLDataType(name="Geometry", category=DataTypeCategory.SPATIAL)
    MULTIPOINT = SQLDataType(name="MultiPoint", category=DataTypeCategory.SPATIAL)
    MULTILINESTRING = SQLDataType(name="MultiLineString", category=DataTypeCategory.SPATIAL)
    MULTIPOLYGON = SQLDataType(name="MultiPolygon", category=DataTypeCategory.SPATIAL)
    GEOMETRYCOLLECTION = SQLDataType(name="GeometryCollection", category=DataTypeCategory.SPATIAL)

    @classmethod
    def get_by_name(cls, col: Dict[str, str]) -> SQLDataType:
        name = col['DATA_TYPE']
        if name.upper() == "LONGTEXT" and str(col.get("COLLATION_NAME", "")).endswith("_bin"):
            return cls.JSON
        if name.upper() == "TINYINT" and str(col.get("COLUMN_TYPE", "")) == "tinyint(1)":
            return cls.BOOLEAN

        return super().get_by_name(name)
