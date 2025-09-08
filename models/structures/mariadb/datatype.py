import sqlalchemy as sa
import sqlalchemy.dialects

import geoalchemy2 as ga

from models.structures import StandardDataType, SQLDataType, DataTypeCategory


class MariaDBDataType(StandardDataType):
    BIT = SQLDataType(name="BIT", category=DataTypeCategory.INTEGER, has_default=True, max_size=64, sa_type=lambda **kwargs: sa.dialects.mysql.BIT(**kwargs))

    TINYINT = SQLDataType(name="TINYINT", category=DataTypeCategory.INTEGER, has_default=True, max_size=127, sa_type=lambda **kwargs: sa.dialects.mysql.TINYINT(display_width=kwargs.get("length")))
    SMALLINT = SQLDataType(name="SMALLINT", category=DataTypeCategory.INTEGER, has_default=True, max_size=32767, sa_type=lambda **kwargs: sa.dialects.mysql.SMALLINT(display_width=kwargs.get("length")))
    INTEGER = SQLDataType(name="INTEGER", alias=["INT"], category=DataTypeCategory.INTEGER, has_default=True, sa_type=lambda **kwargs: sa.dialects.mysql.INTEGER(display_width=kwargs.get("length")))
    MEDIUMINT = SQLDataType(name="MEDIUMINT", category=DataTypeCategory.INTEGER, has_default=True, max_size=8388607, sa_type=lambda **kwargs: sa.dialects.mysql.MEDIUMINT(display_width=kwargs.get("length")))
    BIGINT = SQLDataType(name="BIGINT", category=DataTypeCategory.INTEGER, has_default=True, max_size=9223372036854775807, sa_type=lambda **kwargs: sa.dialects.mysql.BIGINT(display_width=kwargs.get("length")))

    FLOAT = SQLDataType(name="FLOAT", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.mysql.FLOAT(precision=kwargs.get("length"), scale=kwargs.get("scale")))
    DOUBLE = SQLDataType(name="DOUBLE", category=DataTypeCategory.REAL, has_default=True, sa_type=lambda **kwargs: sa.dialects.mysql.DOUBLE(precision=kwargs.get("length"), scale=kwargs.get("scale")))
    DECIMAL = SQLDataType(name="DECIMAL", category=DataTypeCategory.REAL, has_default=True, default_length=20, default_scale=6, max_size=9223372036854775807, sa_type=lambda **kwargs: sa.dialects.mysql.NUMERIC(precision=kwargs.get("precision"), scale=kwargs.get("scale")))

    TIME = SQLDataType(name="TIME", category=DataTypeCategory.TEMPORAL, has_default=True, format="HH:MM:SS", sa_type=lambda **kwargs: sa.Time())
    DATETIME = SQLDataType(name="DATETIME", category=DataTypeCategory.TEMPORAL, has_default=True, format="YYYY-MM-DD HH:MM:SS", sa_type=lambda **kwargs: sa.DateTime())
    TIMESTAMP = SQLDataType(name="TIMESTAMP", category=DataTypeCategory.TEMPORAL, has_default=True, format="YYYY-MM-DD HH:MM:SS", sa_type=lambda **kwargs: sa.TIMESTAMP())

    TINYTEXT = SQLDataType(name="TINYTEXT", category=DataTypeCategory.TEXT, has_default=False, has_length=False, max_size=255, sa_type=lambda **kwargs: sa.dialects.mysql.TINYTEXT(**kwargs))
    MEDIUMTEXT = SQLDataType(name="MEDIUMTEXT", category=DataTypeCategory.TEXT, has_default=False, has_length=False, max_size=16777215, sa_type=lambda **kwargs: sa.dialects.mysql.MEDIUMTEXT(**kwargs))
    LONGTEXT = SQLDataType(name="LONGTEXT", category=DataTypeCategory.TEXT, has_default=False, has_length=False, max_size=4294967295, sa_type=lambda **kwargs: sa.dialects.mysql.LONGTEXT(**kwargs))

    BINARY = SQLDataType(name="BINARY", category=DataTypeCategory.BINARY, has_default=True, default_length=50, sa_type=lambda **kwargs: sa.dialects.mysql.BINARY(**kwargs))
    VARBINARY = SQLDataType(name="VARBINARY", category=DataTypeCategory.BINARY, has_default=True, default_length=50, sa_type=lambda **kwargs: sa.dialects.mysql.VARBINARY())

    TINYBLOB = SQLDataType(name="TINYBLOB", category=DataTypeCategory.BINARY, has_default=False, default_length=50, max_size=255, sa_type=lambda **kwargs: sa.dialects.mysql.TINYBLOB(**kwargs))
    MEDIUMBLOB = SQLDataType(name="MEDIUMBLOB", category=DataTypeCategory.BINARY, has_default=False, max_size=(2 ** 24) - 1, sa_type=lambda **kwargs: sa.dialects.mysql.MEDIUMBLOB(**kwargs))
    LONGBLOB = SQLDataType(name="LONGBLOB", category=DataTypeCategory.BINARY, has_default=False, max_size=(2 ** 32) - 1, sa_type=lambda **kwargs: sa.dialects.mysql.LONGBLOB(**kwargs))

    ENUM = SQLDataType(name="ENUM", category=DataTypeCategory.OTHER, has_default=False, default_set=["'Y'", "'N'"], sa_type=lambda **kwargs: sa.Enum(**kwargs))
    SET = SQLDataType(name="SET", category=DataTypeCategory.OTHER, has_default=False, default_set=["'Value 1'", "'Value 2'"], sa_type=lambda **kwargs: sa.dialects.mysql.SET(**kwargs))

    POINT = SQLDataType(name="Point", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('Point'))
    LINESTRING = SQLDataType(name="LineString", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('LineString'))
    POLYGON = SQLDataType(name="Polygon", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('Polygon'))
    GEOMETRY = SQLDataType(name="Geometry", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('Geometry'))
    MULTIPOINT = SQLDataType(name="MultiPoint", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('MultiPoint'))
    MULTILINESTRING = SQLDataType(name="MultiLineString", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('MultiLineString'))
    MULTIPOLYGON = SQLDataType(name="MultiPolygon", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('MultiPolygon'))
    GEOMETRYCOLLECTION = SQLDataType(name="GeometryCollection", category=DataTypeCategory.SPATIAL, has_default=False, sa_type=lambda **kwargs: ga.Geometry('GeometryCollection'))

    @classmethod
    def get_by_type(cls, type: sa.types.TypeEngine) -> SQLDataType:
        if type.__visit_name__.upper() == "LONGTEXT" and str(getattr(type, "collation", None)).endswith("_bin"):
            return cls.get_by_name("JSON")

        return super().get_by_type(type)
